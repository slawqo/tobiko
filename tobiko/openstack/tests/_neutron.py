from __future__ import absolute_import

import json
import re

from oslo_log import log

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import topology
from tobiko.shell import sh
from tobiko.tripleo import containers
from tobiko.tripleo import has_undercloud
from tobiko.tripleo import pacemaker

LOG = log.getLogger(__name__)


def get_osp_version():
    if not has_undercloud():
        return None
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


def ovn_dbs_are_synchronized(test_case):
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
            test_case.assertEqual(len(ovn_dbs_show_dict[db]),
                                  len(ovn_master_dbs_show_dict[db]))
            for key in ovn_dbs_show_dict[db]:
                test_case.assertEqual(
                    sorted(ovn_dbs_show_dict[db][key]),
                    sorted(ovn_master_dbs_show_dict[db][key]))

    LOG.info("All OVN DBs are synchronized")


def ovn_dbs_vip_bindings(test_case):
    # commands to obtain OVN SB and NB connection strings
    get_ovn_nb_conn_cmd = (
        'crudini --get /var/lib/config-data/puppet-generated/neutron/etc/'
        'neutron/plugins/ml2/ml2_conf.ini ovn ovn_nb_connection')
    get_ovn_sb_conn_cmd = get_ovn_nb_conn_cmd.replace('ovn_nb_connection',
                                                      'ovn_sb_connection')

    controllers = topology.list_openstack_nodes(group='controller')
    ovn_conn_str = {}
    ovn_conn_str['nb'] = sh.execute(get_ovn_nb_conn_cmd,
                                    ssh_client=controllers[0].ssh_client,
                                    sudo=True).stdout.splitlines()[0]
    ovn_conn_str['sb'] = sh.execute(get_ovn_sb_conn_cmd,
                                    ssh_client=controllers[0].ssh_client,
                                    sudo=True).stdout.splitlines()[0]
    ovn_conn = {}
    for db in ('nb', 'sb'):
        ovn_conn[db] = {}
        ipv6 = re.findall(r'\[.*\]', ovn_conn_str[db])
        if len(ipv6) == 1:
            ovn_conn[db]['ip'] = ipv6[0]
        elif len(ipv6) == 0:
            ovn_conn[db]['ip'] = ovn_conn_str[db].split(':')[1]
        else:
            raise RuntimeError('Error parsing ovn db connection string from '
                               'configuration file')
        ovn_conn[db]['port'] = ovn_conn_str[db].split(':')[-1]

    # command to obtain sockets listening on OVN SB and DB DBs
    get_ovn_db_sockets_listening_cmd = \
        "ss -p state listening 'sport = {srcport} and src {srcip}'"

    for controller in controllers:
        for db in ('nb', 'sb'):
            ovn_db_sockets_listening = sh.execute(
                get_ovn_db_sockets_listening_cmd.format(
                    srcport=ovn_conn[db]['port'],
                    srcip=ovn_conn[db]['ip']),
                ssh_client=controller.ssh_client,
                sudo=True).stdout.splitlines()
            test_case.assertEqual(2, len(ovn_db_sockets_listening))
            test_case.assertIn('ovsdb-server', ovn_db_sockets_listening[1])


def test_ovn_dbs_validations():
    if not is_ovn_configured():
        LOG.debug('OVN not configured. OVN DB sync validations skipped')
        return

    test_case = tobiko.get_test_case()

    # run validations
    ovn_dbs_are_synchronized(test_case)
    ovn_dbs_vip_bindings(test_case)


def test_ovs_bridges_mac_table_size():
    test_case = tobiko.get_test_case()
    expected_mac_table_size = '50000'
    get_mac_table_size_cmd = ('ovs-vsctl get bridge {br_name} '
                              'other-config:mac-table-size')
    if is_ovn_configured():
        get_br_mappings_cmd = ('ovs-vsctl get Open_vSwitch . '
                               'external_ids:ovn-bridge-mappings')
    else:
        get_br_mappings_cmd = (
            'crudini --get /var/lib/config-data/puppet-generated/neutron/'
            'etc/neutron/plugins/ml2/openvswitch_agent.ini '
            'ovs bridge_mappings')
    for node in topology.list_openstack_nodes(group='overcloud'):
        try:
            br_mappings_str = sh.execute(get_br_mappings_cmd,
                                         ssh_client=node.ssh_client,
                                         sudo=True).stdout.splitlines()[0]
        except sh.ShellCommandFailed:
            LOG.debug(f"bridge mappings not configured on node '{node.name}'",
                      exc_info=1)
            continue
        br_list = [br_mapping.split(':')[1] for br_mapping in
                   br_mappings_str.replace('"', '').split(',')]
        for br_name in br_list:
            mac_table_size = sh.execute(
                get_mac_table_size_cmd.format(br_name=br_name),
                ssh_client=node.ssh_client, sudo=True).stdout.splitlines()[0]
            test_case.assertEqual(mac_table_size.replace('"', ''),
                                  expected_mac_table_size)
