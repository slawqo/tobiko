from __future__ import absolute_import

import json
import re

from oslo_log import log

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import topology
from tobiko.shell import sh
from tobiko.tripleo import containers
from tobiko.tripleo import pacemaker

LOG = log.getLogger(__name__)


def get_osp_version():
    from tobiko.tripleo import undercloud_ssh_client
    try:
        result = sh.execute("awk '{print $6}' /etc/rhosp-release",
                            ssh_client=undercloud_ssh_client())
    except (sh.ShellCommandFailed, sh.ShellTimeoutExpired):
        LOG.debug("File /etc/rhosp-release not found")
        return None
    else:
        return result.stdout.splitlines()[0]


def is_ovn_configured():
    return containers.ovn_used_on_overcloud()


def build_ovn_db_show_dict(ovn_db_show_str):
    # returns a dictionary with OVN NB or OVN SB DB information
    # each dict key is a section from the OVN DB command output
    # each dict value is a list of strings
    ovn_master_db_dict = {}
    for line in ovn_db_show_str.splitlines():
        if not re.match(r'^\s+', line):
            # if line does not start with a space char, a new section will be
            # started, i.e. a new dict entry
            current_ovn_section = line.strip()
            ovn_master_db_dict[current_ovn_section] = []
        else:
            ovn_master_db_dict[current_ovn_section].append(line.strip())

    return ovn_master_db_dict


def test_neutron_agents_are_alive(timeout=300., interval=5.):
    test_case = tobiko.get_test_case()
    for attempt in tobiko.retry(timeout=timeout, interval=interval):
        LOG.debug("Look for unhealthy Neutron agents...")
        try:
            # get Neutron agent list
            agents = neutron.list_agents()
        except neutron.ServiceUnavailable as ex:
            attempt.check_limits()
            # retry because Neutron server could still be unavailable after
            # a disruption
            LOG.debug(f"Waiting for neutron service... ({ex})")
            continue  # Let retry

        rhosp_version = get_osp_version()
        rhosp_major_release = (int(rhosp_version.split('.')[0])
                               if rhosp_version
                               else None)

        if (rhosp_major_release and rhosp_major_release <= 13 and
                is_ovn_configured()):
            LOG.debug("Neutron list agents should return an empty list with"
                      "OVN and RHOSP releases 13 or earlier")
            test_case.assertEqual([], agents)
            return agents

        if not agents:
            test_case.fail("Neutron has no agents")

        dead_agents = agents.with_items(alive=False)
        if dead_agents:
            dead_agents_details = json.dumps(agents, indent=4, sort_keys=True)
            try:
                test_case.fail("Unhealthy agent(s) found:\n"
                               f"{dead_agents_details}\n")
            except tobiko.FailureException:
                attempt.check_limits()
                # retry because some Neutron agent could still be unavailable
                # after a disruption
                LOG.debug("Waiting for Neutron agents to get alive...\n"
                          f"{dead_agents_details}")
                continue

        LOG.debug(f"All {len(agents)} Neutron agents are alive.")
        return agents


def test_ovn_dbs_are_synchronized():
    if not is_ovn_configured():
        LOG.debug('OVN not configured. OVN DB sync validations skipped')
        return

    test_case = tobiko.get_test_case()

    # declare commands
    search_container_cmd = (
        "%s ps --format '{{.Names}}' -f name=ovn-dbs-bundle" %
        containers.container_runtime_name)
    container_cmd_prefix = ('%s exec -uroot {container}' %
                            containers.container_runtime_name)
    ovndb_sync_cmd = ('ovs-appctl -t /var/run/openvswitch/{ovndb_ctl_file} '
                      'ovsdb-server/sync-status')
    ovndb_show_cmd = '{ovndb} show'
    ovndb_ctl_file_dict = {'nb': 'ovnnb_db.ctl', 'sb': 'ovnsb_db.ctl'}
    ovndb_dict = {'nb': 'ovn-nbctl', 'sb': 'ovn-sbctl'}
    expected_state_active_str = 'state: active'
    expected_state_backup_str = 'state: backup'

    # use ovn master db as a reference
    ovn_master_node_name = pacemaker.get_ovn_db_master_node()
    test_case.assertEqual(1, len(ovn_master_node_name))
    ovn_master_node = topology.get_openstack_node(ovn_master_node_name[0])
    ovn_master_dbs_show_dict = {}
    # obtained the container name
    container_name = sh.execute(
        search_container_cmd,
        ssh_client=ovn_master_node.ssh_client,
        sudo=True).stdout.splitlines()[0]
    for db in ('nb', 'sb'):
        # check its synchronization is active
        sync_cmd = (' '.join((container_cmd_prefix, ovndb_sync_cmd)).
                    format(container=container_name,
                           ovndb_ctl_file=ovndb_ctl_file_dict[db]))
        sync_status = sh.execute(sync_cmd,
                                 ssh_client=ovn_master_node.ssh_client,
                                 sudo=True).stdout
        test_case.assertIn(expected_state_active_str, sync_status)
        # obtain nb and sb show output
        show_cmd = (' '.join((container_cmd_prefix, ovndb_show_cmd)).
                    format(container=container_name, ovndb=ovndb_dict[db]))
        ovn_db_show = sh.execute(
            show_cmd, ssh_client=ovn_master_node.ssh_client, sudo=True).stdout
        ovn_master_dbs_show_dict[db] = build_ovn_db_show_dict(ovn_db_show)

    # ovn dbs are located on the controller nodes
    for node in topology.list_openstack_nodes(group='controller'):
        if node.name == ovn_master_node.name:
            # master node is the reference and do not need to be checked again
            continue
        container_name = sh.execute(
            search_container_cmd,
            ssh_client=node.ssh_client, sudo=True).stdout.splitlines()[0]
        # verify ovn nb and sb dbs are synchronized
        ovn_dbs_show_dict = {}
        for db in ('nb', 'sb'):
            # check its synchronization is active
            sync_cmd = (' '.join((container_cmd_prefix, ovndb_sync_cmd)).
                        format(container=container_name,
                               ovndb_ctl_file=ovndb_ctl_file_dict[db]))
            sync_status = sh.execute(sync_cmd,
                                     ssh_client=node.ssh_client,
                                     sudo=True).stdout
            test_case.assertIn(expected_state_backup_str, sync_status)
            # obtain nb and sb show output
            show_cmd = (' '.join((container_cmd_prefix, ovndb_show_cmd)).
                        format(container=container_name, ovndb=ovndb_dict[db]))
            ovn_db_show = sh.execute(
                show_cmd, ssh_client=node.ssh_client, sudo=True).stdout
            ovn_dbs_show_dict[db] = build_ovn_db_show_dict(ovn_db_show)
            test_case.assertEqual(ovn_dbs_show_dict[db],
                                  ovn_master_dbs_show_dict[db])

    LOG.info("All OVN DBs are synchronized")
