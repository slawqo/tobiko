
from __future__ import absolute_import

from datetime import datetime
import math
import random
import re
import time
import urllib.parse

from oslo_log import log

import tobiko
from tobiko.openstack import glance
from tobiko.openstack import keystone
from tobiko.openstack import stacks
from tobiko.openstack import tests
from tobiko.openstack import topology
from tobiko.tests.faults.ha import test_cloud_recovery
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.tripleo import containers
from tobiko.tripleo import nova
from tobiko.tripleo import pacemaker
from tobiko.tripleo import topology as tripleo_topology


LOG = log.getLogger(__name__)

network_disruption = """
 sudo iptables-save > /home/heat-admin/working.iptables.rules &&
 sudo iptables -I INPUT 1 -m state --state RELATED,ESTABLISHED -j ACCEPT &&
 sudo iptables -I INPUT 2 -p tcp -m state --state NEW -m tcp --dport 22 -j \
 ACCEPT &&
 sudo iptables -I INPUT 3 ! -i lo -j DROP &&
 sudo iptables -I OUTPUT 1 -p tcp --sport 22 -j ACCEPT &&
 sudo iptables -I OUTPUT 2 ! -o lo -j DROP
"""

undisrupt_network = """
 sudo iptables-restore /home/heat-admin/working.iptables.rules
"""
ovn_db_pcs_resource_restart = "sudo pcs resource restart ovn-dbs-bundle"
kill_rabbit = "sudo pkill -9 beam.smp"
kill_galera = "sudo pkill -9 mysqld"
remove_grastate = "sudo rm -rf /var/lib/mysql/grastate.dat"
check_bootstrap = """ps -eo lstart,cmd | grep -v grep|
grep wsrep-cluster-address=gcomm://"""
disable_galera = "sudo pcs resource disable galera --wait=60"
enable_galera = "sudo pcs resource enable galera --wait=90"
disable_haproxy = "sudo pcs resource disable haproxy-bundle --wait=30"
enable_haproxy = "sudo pcs resource enable haproxy-bundle --wait=60"
galera_sst_request = """sudo grep 'wsrep_sst_rsync.*'
/var/log/containers/mysql/mysqld.log"""


class PcsDisableException(tobiko.TobikoException):
    message = "pcs disable didn't shut down the resource"


class PcsEnableException(tobiko.TobikoException):
    message = "pcs enable didn't start the resource"


class GaleraBoostrapException(tobiko.TobikoException):
    message = "Bootstrap should not be done from node without grastate.dat"


class TimestampException(tobiko.TobikoException):
    message = "Timestamp mismatch: sst was requested before grastate removal"


def network_disrupt_node(node_name, disrupt_method=network_disruption):
    disrupt_node(node_name, disrupt_method=disrupt_method)


def network_undisrupt_node(node_name, disrupt_method=undisrupt_network):
    disrupt_node(node_name, disrupt_method=disrupt_method)


def disrupt_node(node_name, disrupt_method=network_disruption):

    # reboot all controllers and wait for ssh Up on them
    # hard reset is simultaneous while soft is sequential
    # method : method of disruption to use : network_disruption |
    # container_restart

    # using ssh_client.connect we use a fire and forget reboot method
    node = tripleo_topology.get_node(node_name)
    node.ssh_client.connect().exec_command(disrupt_method)
    LOG.info('disrupt exec: {} on server: {}'.format(disrupt_method,
                                                     node.name))
    check_overcloud_node_responsive(node)


def reboot_node(node_name, wait=True, reboot_method=sh.hard_reset_method):

    # reboot a node and wait for ssh Up on them
    # hard reset is simultaneous while soft is sequential
    # method : method of disruption to use : reset | network_disruption

    # using ssh_client.connect we use a fire and forget reboot method
    node = tripleo_topology.get_node(node_name)
    sh.reboot_host(ssh_client=node.ssh_client, wait=wait, method=reboot_method)
    LOG.info('disrupt exec: {} on server: {}'.format(reboot_method,
                                                     node.name))


def check_overcloud_node_responsive(node):
    node_checked = sh.execute("hostname",
                              ssh_client=node.ssh_client,
                              expect_exit_status=None).stdout
    LOG.info('{} is up '.format(node_checked))

    tobiko.cleanup_fixture(node.ssh_client)


def network_disrupt_all_controller_nodes(disrupt_method=network_disruption,
                                         exclude_list=None):
    disrupt_all_controller_nodes(disrupt_method=disrupt_method,
                                 exclude_list=exclude_list)


def reset_all_controller_nodes(disrupt_method=sh.hard_reset_method,
                               exclude_list=None):
    disrupt_all_controller_nodes(disrupt_method=disrupt_method,
                                 exclude_list=exclude_list)


def reset_all_controller_nodes_sequentially(
        disrupt_method=sh.hard_reset_method,
        sequentially=True, exclude_list=None):
    disrupt_all_controller_nodes(disrupt_method=disrupt_method,
                                 sequentially=sequentially,
                                 exclude_list=exclude_list)


def disrupt_all_controller_nodes(disrupt_method=sh.hard_reset_method,
                                 sequentially=False, exclude_list=None):
    # reboot all controllers and wait for ssh Up on them
    # method : method of disruptino to use : reset | network_disruption
    # hard reset is simultaneous while soft is sequential
    # exclude_list = list of nodes to NOT reset

    controlplane_groups = ['controller', 'messaging', 'database', 'networker']
    actual_controlplane_groups = tripleo_topology.actual_node_groups(
        controlplane_groups)
    nodes = topology.list_openstack_nodes(group=actual_controlplane_groups)

    # remove excluded nodes from reset list
    if exclude_list:
        nodes = [node for node in nodes if node.name not in exclude_list]

    for controller in nodes:
        if isinstance(disrupt_method, sh.RebootHostMethod):
            reboot_node(controller.name, wait=sequentially,
                        reboot_method=disrupt_method)
        else:
            # using ssh_client.connect we use a fire and forget reboot method
            controller.ssh_client.connect().exec_command(disrupt_method)
            LOG.info('disrupt exec: {} on server: {}'.format(disrupt_method,
                                                             controller.name))
            tobiko.cleanup_fixture(controller.ssh_client)
            if sequentially:
                check_overcloud_node_responsive(controller)
    if not sequentially:
        for controller in topology.list_openstack_nodes(group='controller'):
            check_overcloud_node_responsive(controller)


def reboot_all_controller_nodes(reboot_method=sh.hard_reset_method,
                                sequentially=False, exclude_list=None):
    # reboot all controllers and wait for ssh Up on them
    # method : method of disruptino to use : hard or soft reset
    # hard reset is simultaneous while soft is sequential
    # exclude_list = list of nodes to NOT reset

    controlplane_groups = ['controller', 'messaging', 'database', 'networker']
    actual_controlplane_groups = tripleo_topology.actual_node_groups(
        controlplane_groups)
    nodes = topology.list_openstack_nodes(group=actual_controlplane_groups)

    # remove excluded nodes from reset list
    if exclude_list:
        nodes = [node for node in nodes if node.name not in exclude_list]

    for controller in nodes:
        sh.reboot_host(ssh_client=controller.ssh_client, wait=sequentially,
                       method=reboot_method)
        LOG.info('reboot exec: {} on server: {}'.format(reboot_method,
                                                        controller.name))
        tobiko.cleanup_fixture(controller.ssh_client)
    if not sequentially:
        for controller in topology.list_openstack_nodes(group='controller'):
            check_overcloud_node_responsive(controller)


def get_main_vip():
    """return the ip of the overcloud main vip.
    Retreive an ip address (ipv4/ipv6) from the auth_url."""
    auth_url = keystone.default_keystone_credentials().auth_url
    auth_url_parsed = urllib.parse.urlsplit(auth_url)
    return auth_url_parsed.hostname


def get_main_vip_controller(main_vip):
    """return the controller hostname ,
    which is holding the main_vip pacemaker resource"""
    main_vim_controller = pacemaker.get_overcloud_nodes_running_pcs_resource(
        resource=f"ip-{main_vip}")[0]
    return main_vim_controller


def delete_evacuable_tagged_image():
    # delete evacuable tagged image because it prevents
    # non tagged evacuations if exists
    for img in glance.list_images():
        if 'evacuable' in img['tags']:
            glance.delete_image(img.id)


def disrupt_controller_main_vip(disrupt_method=sh.hard_reset_method,
                                inverse=False):

    # reset the controller holding the main vip (os_auth_url)
    # ip resource (managed via pacemaker)
    # find main vip by getting it from
    main_vip = get_main_vip()

    # find the node holding that resource via :

    main_vip_controller = get_main_vip_controller(main_vip)

    if isinstance(disrupt_method, sh.RebootHostMethod):
        if inverse:
            reboot_all_controller_nodes(reboot_method=disrupt_method,
                                        exclude_list=[main_vip_controller])
        else:
            reboot_node(main_vip_controller, reboot_method=disrupt_method)
    else:
        if inverse:
            # inverse the nodes reset selection
            disrupt_all_controller_nodes(disrupt_method=disrupt_method,
                                         exclude_list=[main_vip_controller])
        else:
            # get that node's ssh_client and reset it
            disrupt_node(main_vip_controller, disrupt_method=disrupt_method)


def reset_controller_main_vip():
    disrupt_controller_main_vip(disrupt_method=sh.hard_reset_method)


def reset_controllers_non_main_vip():
    disrupt_controller_main_vip(disrupt_method=sh.hard_reset_method,
                                inverse=True)


def crash_controller_main_vip():
    disrupt_controller_main_vip(disrupt_method=sh.crash_method)


def crash_controllers_non_main_vip():
    disrupt_controller_main_vip(disrupt_method=sh.crash_method,
                                inverse=True)


def network_disrupt_controller_main_vip():
    disrupt_controller_main_vip(disrupt_method=network_disruption)
    LOG.info('waiting 60s to avoid race conditions...')
    time.sleep(60.0)


def network_undisrupt_controller_main_vip():
    disrupt_controller_main_vip(disrupt_method=undisrupt_network)


def network_disrupt_controllers_non_main_vip():
    disrupt_controller_main_vip(disrupt_method=network_disruption,
                                inverse=True)


def network_undisrupt_controllers_non_main_vip():
    disrupt_controller_main_vip(disrupt_method=undisrupt_network,
                                inverse=True)


def reset_all_compute_nodes(hard_reset=False):

    # reboot all computes and wait for ssh Up on them
    # hard reset is simultaneous while soft is sequential
    if hard_reset:
        reset_method = sh.hard_reset_method
    else:
        reset_method = sh.soft_reset_method
    for compute in topology.list_openstack_nodes(group='compute'):
        # using ssh_client.connect we use a fire and forget reboot method
        sh.reboot_host(ssh_client=compute.ssh_client, wait=False,
                       method=reset_method)
        LOG.info('reboot exec:  {} on server: {}'.format(reset_method,
                                                         compute.name))
        tobiko.cleanup_fixture(compute.ssh_client)

    for compute in topology.list_openstack_nodes(group='compute'):
        compute_checked = sh.execute("hostname", ssh_client=compute.ssh_client,
                                     expect_exit_status=None).stdout
        LOG.info('{} is up '.format(compute_checked))


def reset_ovndb_pcs_master_resource():
    """restart ovndb pacemaker resource
    this method only restart the resource running on the controller with is
    acting as Master"""
    node = pacemaker.get_overcloud_nodes_running_pcs_resource(
        resource_type='(ocf::ovn:ovndb-servers):', resource_state='Master')[0]
    ovn_db_pcs_master_resource_restart = (ovn_db_pcs_resource_restart + ' ' +
                                          node)
    disrupt_node(node, disrupt_method=ovn_db_pcs_master_resource_restart)


def reset_ovndb_pcs_resource():
    """restart ovndb pacemaker resource
    this method restart the whole resource, i.e. on all the controller nodes"""
    node = pacemaker.get_overcloud_nodes_running_pcs_resource(
        resource_type='(ocf::ovn:ovndb-servers):', resource_state='Master')[0]
    disrupt_node(node, disrupt_method=ovn_db_pcs_resource_restart)


def reset_ovndb_master_container():
    """get and restart the ovndb master container
    use of partial name :  resource: ovn-dbs-bundle-0 =>
    container: ovn-dbs-bundle-podman-0 or ovn-dbs-bundle-docker-0"""
    node = pacemaker.get_overcloud_nodes_running_pcs_resource(
        resource_type='(ocf::ovn:ovndb-servers):', resource_state='Master')[0]
    resource = pacemaker.get_overcloud_resource(
        resource_type='(ocf::ovn:ovndb-servers):', resource_state='Master')
    resource = resource[0].rsplit('-', 1)[0]
    containers.action_on_container('restart',
                                   partial_container_name=resource,
                                   container_host=node)


def kill_rabbitmq_service():
    """kill a rabbit process on a random controller,
    check in pacemaker it is down"""
    if tripleo_topology.is_composable_roles_env():
        nodes = topology.list_openstack_nodes(group='messaging')
    else:
        nodes = topology.list_openstack_nodes(group='controller')
    node = random.choice(nodes)
    sh.execute(kill_rabbit, ssh_client=node.ssh_client)
    LOG.info('kill rabbit: {} on server: {}'.format(kill_rabbit,
             node.name))
    retry = tobiko.retry(timeout=30, interval=5)
    for _ in retry:
        if not(pacemaker.PacemakerResourcesStatus().
               rabbitmq_resource_healthy()):
            return


def kill_all_galera_services():
    """kill all galera processes,
    check in pacemaker it is down"""
    if tripleo_topology.is_composable_roles_env():
        nodes = topology.list_openstack_nodes(group='database')
    else:
        nodes = topology.list_openstack_nodes(group='controller')
    for node in nodes:
        sh.execute(kill_galera, ssh_client=node.ssh_client)
        LOG.info('kill galera: {} on server: {}'.format(kill_galera,
                 node.name))
    retry = tobiko.retry(timeout=30, interval=5)
    for _ in retry:
        if not(pacemaker.PacemakerResourcesStatus().
               galera_resource_healthy()):
            return


def remove_all_grastate_galera():
    """shut down galera properly,
    remove all grastate"""
    if tripleo_topology.is_composable_roles_env():
        nodes = topology.list_openstack_nodes(group='database')
    else:
        nodes = topology.list_openstack_nodes(group='controller')
    LOG.info('shut down galera: {} on all servers: {}'.
             format(disable_galera, nodes))
    if "resource 'galera' is not running on any node" not in\
            sh.execute(disable_galera, ssh_client=nodes[0].ssh_client).stdout:
        raise PcsDisableException()
    for node in nodes:
        sh.execute(remove_grastate, ssh_client=node.ssh_client)
    LOG.info('enable back galera: {} on all servers: {}'.
             format(enable_galera, nodes))
    if "resource 'galera' is master on node" not in\
            sh.execute(enable_galera, ssh_client=nodes[0].ssh_client).stdout:
        raise PcsEnableException()


def remove_one_grastate_galera():
    """shut down galera properly,
    delete /var/lib/mysql/grastate.dat in a random node,
    check that bootstrap is done from a node with grastate"""
    if tripleo_topology.is_composable_roles_env():
        nodes = topology.list_openstack_nodes(group='database')
    else:
        nodes = topology.list_openstack_nodes(group='controller')
    node = random.choice(nodes)
    LOG.info('disable haproxy-bunble')
    if "resource 'haproxy-bundle' is not running on any node" not in\
            sh.execute(disable_haproxy, ssh_client=node.ssh_client).stdout:
        raise PcsDisableException()
    LOG.info('shut down galera: {} on all servers: {}'.
             format(disable_galera, nodes))
    if "resource 'galera' is not running on any node" not in\
            sh.execute(disable_galera, ssh_client=node.ssh_client).stdout:
        raise PcsDisableException()
    LOG.info('remove grastate: {} on server: {}'.format(remove_grastate,
                                                        node.name))
    sh.execute(remove_grastate, ssh_client=node.ssh_client)
    LOG.info('enable back galera: {} on all servers: {}'.
             format(enable_galera, nodes))
    if "resource 'galera' is master on node" not in\
            sh.execute(enable_galera, ssh_client=node.ssh_client).stdout:
        raise PcsEnableException()
    LOG.info('enable haproxy-bundle')
    if "resource 'haproxy-bundle' is running on node" not in\
            sh.execute(enable_haproxy, ssh_client=node.ssh_client).stdout:
        raise PcsEnableException()
    # gcomm:// without args means that bootstrap is done from this node
    bootstrap = sh.execute(check_bootstrap, ssh_client=node.ssh_client).stdout
    if re.search('wsrep-cluster-address=gcomm:// --', bootstrap) is not None:
        raise GaleraBoostrapException()
    lastDate = re.findall(r"\w{,3}\s*\w{,3}\s*\d{,2}\s*\d{,2}:\d{,2}:\d{,2}\s*"
                          r"\d{4}", bootstrap)[-1]
    return node, lastDate


def request_galera_sst():
    """remove_one_grastate_galera,
    check that sst is requested by a node with grastate"""
    node, date = remove_one_grastate_galera()
    bootstrapDate = datetime.strptime(date, '%a %b %d %H:%M:%S %Y')
    retry = tobiko.retry(timeout=30, interval=5)
    for _ in retry:
        sst_req = sh.execute(galera_sst_request,
                             ssh_client=node.ssh_client).stdout
        if sst_req:
            break
    sstDate = datetime.strptime(re.findall
                                (r"\d{4}-\d{,2}-\d{,2}\s*\d{,2}:\d{,2}:\d{,2}",
                                 sst_req)[-1], '%Y-%m-%d %H:%M:%S')
    if bootstrapDate > sstDate:
        raise TimestampException


def evac_failover_compute(compute_host, failover_type=sh.hard_reset_method):
    """disrupt a compute, to trigger it's instance-HA evacuation
    failover_type=hard_reset_method etc.."""
    if failover_type in (sh.hard_reset_method, sh.soft_reset_method):
        reboot_node(compute_host, reboot_method=failover_type)
    else:
        disrupt_node(compute_host, disrupt_method=failover_type)


def check_iha_evacuation(failover_type=None, vm_type=None):
    """check vms on compute host,disrupt compute host,
    check all vms evacuated and pingable"""
    for iteration in range(2):
        LOG.info(f'Begin IHA tests iteration {iteration}')
        LOG.info('create 2 vms')
        tests.test_servers_creation(number_of_servers=2)
        compute_host = nova.get_random_compute_with_vms_name()
        vms_starting_state_df = nova.get_compute_vms_df(compute_host)
        if vm_type == 'shutoff':
            nova.stop_all_instances()
        if vm_type == 'evac_image_vm':
            evac_vm_stack = tests.test_evacuable_server_creation()
            evac_vm_id = nova.get_stack_server_id(evac_vm_stack)
            org_nova_evac_df = nova.vm_df(evac_vm_id, nova.get_vms_table())
        if not vm_type == 'shutoff':
            nova.check_df_vms_ping(vms_starting_state_df)
        LOG.info(f'perform a failover on {compute_host}')
        evac_failover_compute(compute_host, failover_type=failover_type)
        test_cloud_recovery.overcloud_health_checks(passive_checks_only=True)
        if vm_type == 'evac_image_vm':
            nova.check_vm_evacuations(vms_df_old=org_nova_evac_df,
                                      compute_host=compute_host,
                                      timeout=600,
                                      check_no_evacuation=True)
            # delete evacuable tagged image because it prevents
            # non tagged evacuations if exists
            delete_evacuable_tagged_image()
            new_nova_evac_df = nova.vm_df(evac_vm_id, nova.get_vms_table())
            nova.check_vm_evacuations(org_nova_evac_df, new_nova_evac_df)
        else:
            nova.check_vm_evacuations(vms_df_old=vms_starting_state_df,
                                      compute_host=compute_host,
                                      timeout=600)
        LOG.info('check evac is Done')
        if not vm_type == 'shutoff':
            nova.check_df_vms_ping(vms_starting_state_df)


def check_iha_evacuation_evac_image_vm():
    check_iha_evacuation(failover_type=sh.hard_reset_method,
                         vm_type='evac_image_vm')


def check_iha_evacuation_hard_reset():
    check_iha_evacuation(failover_type=sh.hard_reset_method)


def check_iha_evacuation_network_disruption():
    check_iha_evacuation(failover_type=network_disruption)


def check_iha_evacuation_hard_reset_shutoff_instance():
    check_iha_evacuation(failover_type=sh.hard_reset_method, vm_type='shutoff')


def test_controllers_shutdown():
    test_case = tobiko.get_test_case()

    all_nodes = topology.list_openstack_nodes(group='controller')
    if len(all_nodes) < 3:
        tobiko.skip_test('It requires at least three controller nodes')

    all_node_names = [node.name for node in all_nodes]
    LOG.info("Ensure all controller nodes are running: "
             f"{all_node_names}")
    for node in all_nodes:
        node.power_on_overcloud_node()
    topology.assert_reachable_nodes(all_nodes)

    LOG.debug('Check VM is running while all controllers nodes are on')
    nova_server = tobiko.setup_fixture(stacks.CirrosServerStackFixture)
    nova_server_ip = nova_server.ip_address
    ping.assert_reachable_hosts([nova_server_ip])

    quorum_level = math.ceil(0.5 * len(all_nodes))
    assert quorum_level >= len(all_nodes) - quorum_level
    nodes = random.sample(all_nodes, quorum_level)
    node_names = [node.name for node in nodes]
    LOG.info(f"Power off {quorum_level} random controller nodes: "
             f"{node_names}")
    for node in nodes:
        node.power_off_overcloud_node()
        test_case.addCleanup(node.power_on_overcloud_node)
    topology.assert_unreachable_nodes(nodes, retry_count=1)
    topology.assert_reachable_nodes(node
                                    for node in all_nodes
                                    if node not in nodes)

    LOG.debug('Check whenever VM is still running while some "'
              '"controllers nodes are off')
    reachable, unreachable = ping.ping_hosts([nova_server_ip],
                                             count=1)
    if reachable:
        LOG.debug(f"VM ips are reachable: {reachable}")
    if unreachable:
        LOG.debug(f"VM is are unreachable: {unreachable}")
    # TODO what do we expect here: VM reachable or unreachable?

    random.shuffle(nodes)
    LOG.info(f"Power on controller nodes: {node_names}")
    for node in nodes:
        node.power_on_overcloud_node()

    LOG.debug("Check all controller nodes are running again: "
              f"{all_node_names}")
    topology.assert_reachable_nodes(all_nodes, retry_timeout=600.)

    LOG.debug('Check VM is running while all controllers nodes are on')
    ping.assert_reachable_hosts([nova_server_ip])
