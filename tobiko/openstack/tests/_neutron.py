from __future__ import absolute_import

import collections
import functools
import json
import re
import typing

from keystoneauth1 import exceptions
from oslo_log import log

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import topology
from tobiko.shell import ip
from tobiko.shell import sh
from tobiko.tripleo import pacemaker

LOG = log.getLogger(__name__)


# Supported OVN DB service models
RAFT = 'RAFT'
HA = 'HA'
# Supported OVN databases
OVNDBS = ('nb', 'sb')


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

    for section in ovn_master_db_dict:
        ovn_master_db_dict[section].sort()
    return ovn_master_db_dict


def test_neutron_agents_are_alive(timeout=300., interval=5.) \
        -> tobiko.Selection[neutron.NeutronAgentType]:
    for attempt in tobiko.retry(timeout=timeout, interval=interval):
        LOG.debug("Look for unhealthy Neutron agents...")
        try:
            # get Neutron agent list
            agents = neutron.list_agents()
        except (neutron.ServiceUnavailable,
                neutron.NeutronClientException,
                exceptions.connection.ConnectFailure) as ex:
            if attempt.is_last:
                raise
            else:
                # retry because Neutron server could still be unavailable
                # after a disruption
                LOG.debug(f"Waiting for neutron service... ({ex})")
                continue  # Let retry

        dead_agents = agents.with_items(alive=False)
        if dead_agents:
            dead_agents_details = json.dumps(agents, indent=4, sort_keys=True)
            if attempt.is_last:
                tobiko.fail("Unhealthy agent(s) found:\n"
                            f"{dead_agents_details}\n")
            else:
                # retry because some Neutron agent could still be unavailable
                # after a disruption
                LOG.debug("Waiting for Neutron agents to get alive...\n"
                          f"{dead_agents_details}")
                continue

        LOG.debug(f"All {len(agents)} Neutron agents are alive.")
        break
    else:
        raise RuntimeError("Retry loop broken")

    return agents


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

    # TODO(eolivare): add support to verify ssl connections
    if 'ssl' in ovn_conn_str['nb'] or 'ssl' in ovn_conn_str['sb']:
        LOG.debug('tobiko does not support to verify ovn-db connections when '
                  'they are based on ssl')
        return

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

    # ovn db sockets might be centrillized or distributed
    # that depends on the openstack version under test
    ovn_db_sockets_centrallized = topology.verify_osp_version(
        '14.0', lower=True)

    # command to obtain sockets listening on OVN SB and DB DBs
    get_ovn_db_sockets_listening_cmd = \
        "ss -p state listening 'sport = {srcport} and src {srcip}'"

    num_db_sockets = 0
    for controller in controllers:
        for db in ('nb', 'sb'):
            ovn_db_sockets_listening = sh.execute(
                get_ovn_db_sockets_listening_cmd.format(
                    srcport=ovn_conn[db]['port'],
                    srcip=ovn_conn[db]['ip']),
                ssh_client=controller.ssh_client,
                sudo=True).stdout.splitlines()
            if ovn_db_sockets_centrallized:
                if 2 == len(ovn_db_sockets_listening):
                    num_db_sockets += 1
                    test_case.assertIn('ovsdb-server',
                                       ovn_db_sockets_listening[1])
            else:
                num_db_sockets += 1
                test_case.assertEqual(2, len(ovn_db_sockets_listening))
                test_case.assertIn('ovsdb-server', ovn_db_sockets_listening[1])

    if ovn_db_sockets_centrallized:
        test_case.assertEqual(2, num_db_sockets)
    else:
        test_case.assertEqual(2 * len(controllers), num_db_sockets)


def ovn_dbs_are_synchronized(test_case):
    """Check that OVN DBs are syncronized across all controller nodes"""
    db_model = get_ovn_db_service_model()
    db_sync_status = get_ovn_db_sync_status()
    if db_model == HA:
        # In Active-Backup service model we expect the same controller to be
        # active for both databases. This controller node should be configured
        # for virtual IP in pacemaker. Other controllers should be in backup
        # state
        ovn_master_node_name = pacemaker.get_ovn_db_master_node()
        test_case.assertEqual(1, len(ovn_master_node_name))
        ovn_master_node = topology.get_openstack_node(ovn_master_node_name[0])
        LOG.debug("OVN DB master node hostname is: {}".format(
            ovn_master_node.hostname))
        for db in OVNDBS:
            for controller, state in db_sync_status[db]:
                if controller == ovn_master_node.hostname:
                    test_case.assertEqual('active', state)
                else:
                    test_case.assertEqual('backup', state)
    elif db_model == RAFT:
        # In clustered database service model we expect all databases to be
        # active
        for db in OVNDBS:
            for _, state in db_sync_status[db]:
                test_case.assertEqual('active', state)
    dumps = dump_ovn_databases()
    for db in OVNDBS:
        if len(dumps[db]) <= 1:
            # Database from a single node is available
            # so there is nothing to compare it with
            continue
        for i in range(1, len(dumps[db])):
            test_case.assertEqual(dumps[db][0][1], dumps[db][i][1])
            LOG.debug('OVN {} databases are equal on {} and {}'.format(
                db, dumps[db][0][0], dumps[db][i][0]))


def find_ovn_db_sockets():
    """Search for OVN DB sockets

    Unix sockets are useful in case there is a need to check the local
    database.
    """
    node_ssh = topology.list_openstack_nodes(group='controller')[0].ssh_client
    socs = sh.execute('ss -ax state listening', ssh_client=node_ssh, sudo=True)
    sockets = {}
    for db in OVNDBS:
        pattern = '[^ ]*ovn{}_db.sock'.format(db)
        sockets[db] = re.search(pattern, socs.stdout, re.MULTILINE).group()
    LOG.debug('OVN DB socket files found: {}'.format(sockets))
    return sockets


def dump_ovn_databases():
    """Dump NB and SB on each controller node"""
    from tobiko.tripleo import containers
    runtime_name = containers.get_container_runtime_name()
    sockets = find_ovn_db_sockets()
    db_mode = get_ovn_db_service_model()
    # To be able to connect to local database in RAFT environment
    # --no-leader-only parameter should be specified
    no_leader = (' --no-leader-only' if db_mode == 'RAFT' else '')
    dumps = {}
    for node in topology.list_openstack_nodes(group='controller'):
        for db in OVNDBS:
            connection = '--db=unix:{}{}'.format(sockets[db], no_leader)
            cmd = '{} exec -uroot ovn_controller ovn-{}ctl {} show'.format(
                    runtime_name, db, connection)
            LOG.debug('Dump {} database on {} with following command: {}'.
                      format(db, node.hostname, cmd))
            output = sh.execute(cmd, ssh_client=node.ssh_client, sudo=True)
            dumps.setdefault(db, [])
            dumps[db].append(
                    [node.hostname, build_ovn_db_show_dict(output.stdout)])
    return dumps


def find_ovn_db_ctl_files():
    """Search for ovnsb_db.ctl and ovnnb_db.ctl files"""
    node = topology.list_openstack_nodes(group='controller')[0]
    ctl_files = {}
    for db in OVNDBS:
        cmd = 'find /var/ -name ovn{}_db.ctl'.format(db)
        found = sh.execute(cmd, ssh_client=node.ssh_client, sudo=True).stdout
        ctl_files[db] = found.strip()
    LOG.debug('OVN DB ctl files found: {}'.format(ctl_files))
    return ctl_files


def get_ovn_db_sync_status():
    """Query sync status for NB and SB for each controller node"""
    db_sync_status = {}
    ctl_files = find_ovn_db_ctl_files()
    for node in topology.list_openstack_nodes(group='controller'):
        for db in OVNDBS:
            ctl_file = ctl_files[db]
            cmd = 'ovs-appctl -t {} ovsdb-server/sync-status'.format(ctl_file)
            output = sh.execute(cmd, ssh_client=node.ssh_client, sudo=True)
            db_status = output.stdout
            if 'state: active' in db_status:
                status = 'active'
            elif 'state: backup' in db_status:
                status = 'backup'
            else:
                status = 'unknown'
            db_sync_status.setdefault(db, [])
            db_sync_status[db].append([node.hostname, status])
    LOG.debug('OVN DB status for all controllers: {}'.format(db_sync_status))
    return db_sync_status


class InvalidDBServiceModel(tobiko.TobikoException):
    message = "Database service model is not supported:\n{db_string}"


@functools.lru_cache()
def get_ovn_db_service_model():
    """Show in which mode OVN databases are configured

    There are two modes currently supported:
     - RAFT aka clustered service model (default starting OSP17.0)
     - HA aka Active-Backup service model (default for pre-OSP17.0 versions)

    For more information:
    https://docs.openvswitch.org/en/latest/ref/ovsdb.7/#service-models
    """
    controller0 = topology.list_openstack_nodes(group='controller')[0]
    db_info = sh.execute('find / -name ovnnb_db.db | xargs sudo head -n 1',
                         ssh_client=controller0.ssh_client, sudo=True)
    if 'CLUSTER' in db_info.stdout:
        return RAFT
    elif 'JSON' in db_info.stdout:
        return HA
    else:
        LOG.error('Only RAFT and HA database service models are supported')
        raise InvalidDBServiceModel(db_string=db_info.stdout)


def test_ovn_dbs_validations():
    if not neutron.has_ovn():
        LOG.debug('OVN not configured. OVN DB sync validations skipped')
        return

    test_case = tobiko.get_test_case()

    db_service_model = get_ovn_db_service_model()
    LOG.debug('OVN DBs are configured in {} mode'.format(db_service_model))
    ovn_dbs_are_synchronized(test_case)
    if db_service_model == HA:
        ovn_dbs_vip_bindings(test_case)


def test_ovs_bridges_mac_table_size():
    test_case = tobiko.get_test_case()
    expected_mac_table_size = '50000'
    get_mac_table_size_cmd = ('ovs-vsctl get bridge {br_name} '
                              'other-config:mac-table-size')
    if neutron.has_ovn():
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


OPENSTACK_NODE_GROUP = re.compile(r'(compute|controller|overcloud)')
OVS_NAMESPACE = re.compile(r'(qrouter.*|qdhcp.*|snat.*|fip.*)')


def test_ovs_namespaces_are_absent(
        group: typing.Pattern[str] = OPENSTACK_NODE_GROUP,
        namespace: typing.Pattern[str] = OVS_NAMESPACE):
    nodes = topology.list_openstack_nodes(group=group)

    namespaces: typing.Dict[str, typing.List[str]] = (
        collections.defaultdict(list))
    for node in nodes:
        for node_namespace in ip.list_network_namespaces(
                ssh_client=node.ssh_client, sudo=True):
            if namespace.match(node_namespace):
                namespaces[node.name].append(node_namespace)
    namespaces = dict(namespaces)

    test_case = tobiko.get_test_case()
    test_case.assertEqual(
        {}, dict(namespaces),
        f"OVS namespace(s) found on OpenStack nodes: {namespaces}")


OVS_INTERFACE = re.compile(r'(qvo.*|qvb.*|qbr.*|qr.*|qg.*|fg.*|sg.*)')


def test_ovs_interfaces_are_absent(
        group: typing.Pattern[str] = OPENSTACK_NODE_GROUP,
        interface: typing.Pattern[str] = OVS_INTERFACE):
    nodes = topology.list_openstack_nodes(group=group)

    interfaces: typing.Dict[str, typing.List[str]] = (
        collections.defaultdict(list))
    for node in nodes:
        for node_interface in ip.list_network_interfaces(
                ssh_client=node.ssh_client, sudo=True):
            if interface.match(node_interface):
                interfaces[node.name].append(node_interface)
    interfaces = dict(interfaces)

    test_case = tobiko.get_test_case()
    test_case.assertEqual(
        {}, interfaces,
        f"OVS interface(s) found on OpenStack nodes: {interfaces}")
