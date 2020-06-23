
from __future__ import absolute_import

import re

import tobiko
from tobiko.shell import sh
from tobiko.openstack import topology
from tobiko.tripleo import topology as tripleo_topology
from tobiko.openstack import keystone
from tobiko.tripleo import pacemaker
from tobiko.tripleo import containers
from tobiko.tripleo import nova
from oslo_log import log
from tobiko.tests.faults.ha import test_cloud_recovery


LOG = log.getLogger(__name__)

hard_reset_method = 'sudo chmod o+w /proc/sysrq-trigger;' \
               'sudo echo b > /proc/sysrq-trigger'

soft_reset_method = 'sudo reboot'

network_disruption = """
 sudo iptables-save -f /root/working.iptables.rules &&
 sudo iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT &&
 sudo iptables -A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j \
 ACCEPT &&
 sudo iptables -A INPUT ! -i lo -j REJECT --reject-with icmp-host-prohibited &&
 sudo iptables -A OUTPUT -p tcp --sport 22 -j ACCEPT &&
 sudo iptables -A OUTPUT ! -o lo -j REJECT --reject-with icmp-host-prohibited
"""

undisrupt_network = """
 sudo iptables-restore /root/working.iptables.rules
"""
ovn_db_pcs_resource_restart = """sudo pcs resource restart ovn-dbs-bundle"""


def get_node(node_name):
    node_name = node_name.split('.')[0]
    return [node for node in topology.list_openstack_nodes() if
            node.name == node_name][0]


def network_disrupt_node(node_name, disrupt_method=network_disruption):
    disrupt_node(node_name, disrupt_method=disrupt_method)


def network_undisrupt_node(node_name, disrupt_method=undisrupt_network):
    disrupt_node(node_name, disrupt_method=disrupt_method)


def reset_node(node_name, disrupt_method=hard_reset_method):
    disrupt_node(node_name, disrupt_method=disrupt_method)


def disrupt_node(node_name, disrupt_method=hard_reset_method):

    # reboot all controllers and wait for ssh Up on them
    # hard reset is simultaneous while soft is sequential
    # method : method of disruptino to use : reset | network_disruption

    # using ssh_client.connect we use a fire and forget reboot method
    node = get_node(node_name)
    node.ssh_client.connect().exec_command(disrupt_method)
    LOG.info('disrupt exec: {} on server: {}'.format(disrupt_method,
                                                     node.name))
    check_overcloud_node_responsive(node)


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


def reset_all_controller_nodes(disrupt_method=hard_reset_method,
                               exclude_list=None):
    disrupt_all_controller_nodes(disrupt_method=disrupt_method,
                                 exclude_list=exclude_list)


def reset_all_controller_nodes_sequentially(disrupt_method=hard_reset_method,
                                            sequentially=True,
                                            exclude_list=None):
    disrupt_all_controller_nodes(disrupt_method=disrupt_method,
                                 sequentially=sequentially,
                                 exclude_list=exclude_list)


def disrupt_all_controller_nodes(disrupt_method=hard_reset_method,
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


def get_main_vip():
    """return the ip of the overcloud main_vip"""
    credentials = keystone.default_keystone_credentials()
    auth_url = credentials.auth_url
    auth_url_ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', auth_url)[0]
    return auth_url_ip


def get_main_vip_controller(main_vip):
    """return the controller hostname ,
    which is holding the main_vip pacemaker resource"""
    main_vim_controller = pacemaker.get_overcloud_nodes_running_pcs_resource(
        resource=f"ip-{main_vip}")[0]
    return main_vim_controller


def disrupt_controller_main_vip(disrupt_method=hard_reset_method,
                                inverse=False):

    # reset the controller holding the main vip (os_auth_url)
    # ip resource (managed via pacemaker)
    # find main vip by getting it from
    main_vip = get_main_vip()

    # find the node holding that resource via :

    main_vim_controller = get_main_vip_controller(main_vip)

    if inverse:
        # inverse the nodes reset selection
        disrupt_all_controller_nodes(disrupt_method=disrupt_method,
                                     exclude_list=[main_vim_controller])
    else:
        # get that node's ssh_client and reset it
        disrupt_node(main_vim_controller, disrupt_method=disrupt_method)


def reset_controller_main_vip():
    disrupt_controller_main_vip(disrupt_method=hard_reset_method)


def reset_controllers_non_main_vip():
    disrupt_controller_main_vip(disrupt_method=hard_reset_method, inverse=True)


def network_disrupt_controller_main_vip():
    disrupt_controller_main_vip(disrupt_method=network_disruption)


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
        reset_method = hard_reset_method
    else:
        reset_method = soft_reset_method
    for compute in topology.list_openstack_nodes(group='compute'):
        # using ssh_client.connect we use a fire and forget reboot method
        compute.ssh_client.connect().exec_command(reset_method)
        LOG.info('reboot exec:  {} on server: {}'.format(reset_method,
                                                         compute.name))
        tobiko.cleanup_fixture(compute.ssh_client)

    for compute in topology.list_openstack_nodes(group='compute'):
        compute_checked = sh.execute("hostname", ssh_client=compute.ssh_client,
                                     expect_exit_status=None).stdout
        LOG.info('{} is up '.format(compute_checked))


def reset_ovndb_master_resource():
    """restart ovndb pacemaker resource"""
    disrupt_node('controller-0', disrupt_method=ovn_db_pcs_resource_restart)


def reset_ovndb_master_container():
    """get and restart the ovndb master container
    use of partial name :  resource: ovn-dbs-bundle-0 =>
    container: ovn-dbs-bundle-podman-2"""
    node = pacemaker.get_overcloud_nodes_running_pcs_resource(
        resource_type='(ocf::ovn:ovndb-servers):', resource_state='Master')[0]
    resource = pacemaker.get_overcloud_resource(
        resource_type='(ocf::ovn:ovndb-servers):', resource_state='Master')
    resource = resource[0].rsplit('-', 1)[0]
    containers.action_on_container('restart',
                                   partial_container_name=resource,
                                   container_host=node)


def evac_failover_compute(compute_host, failover_type=hard_reset_method):
    """disrupt a compute, to trigger it's instance-HA evacuation
    failover_type=hard_reset_method etc.."""
    reset_node(compute_host, disrupt_method=failover_type)


def check_iha_evacuation(failover_type=None, vm_type=None):
    """check vms on compute host,disrupt compute host,
    check all vms evacuated and pingable"""
    for iteration in range(2):
        LOG.info(f'Beign IHA tests iteration {iteration}')
        LOG.info('creatr 4 vms')
        nova.create_multiple_unique_vms(n_vms=2)
        compute_host = nova.get_random_compute_with_vms_name()
        vms_starting_state_df = nova.get_compute_vms_df(compute_host)
        if vm_type == 'shutoff':
            nova.stop_all_instances()
        if vm_type == 'evac_image_vm':
            evac_vm_stack = nova.random_vm_create_evacuable_image_tag()
            evac_vm_id = nova.get_stack_server_id(evac_vm_stack)
            org_nova_evac_df = nova.vm_df(evac_vm_id, nova.get_vms_table())
        nova.check_df_vms_ping(vms_starting_state_df)
        LOG.info(f'perform a failover on {compute_host}')
        evac_failover_compute(compute_host, failover_type=failover_type)
        test_cloud_recovery.overcloud_health_checks(passive_checks_only=True)
        vms_new_state_df = nova.get_compute_vms_df(compute_host)
        if vm_type == 'evac_image_vm':
            nova.check_vm_evacuations(vms_df_old=org_nova_evac_df,
                                      vms_df_new=vms_new_state_df,
                                      check_no_evacuation=True)
            new_nova_evac_df = nova.vm_df(evac_vm_id, nova.get_vms_table())
            nova.check_vm_evacuations(org_nova_evac_df, new_nova_evac_df)
        LOG.info('check evac is Done')
        nova.check_vm_evacuations(vms_df_old=vms_starting_state_df,
                                  vms_df_new=vms_new_state_df)
        nova.check_df_vms_ping(vms_starting_state_df)


def check_iha_evacuation_evac_image_vm():
    check_iha_evacuation(failover_type=hard_reset_method,
                         vm_type='evac_image_vm')


def check_iha_evacuation_hard_reset():
    check_iha_evacuation(failover_type=hard_reset_method)


def check_iha_evacuation_network_disruption():
    check_iha_evacuation(failover_type=network_disruption)


def check_iha_evacuation_hard_reset_shutoff_instance():
    check_iha_evacuation(failover_type=hard_reset_method, vm_type='shutoff')
