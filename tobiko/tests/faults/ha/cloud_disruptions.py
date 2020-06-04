
from __future__ import absolute_import

import re

import tobiko
from tobiko.shell import sh
from tobiko.openstack import topology
from tobiko.tripleo import topology as tripleo_topology
from tobiko.openstack import keystone
from tobiko.tripleo import pacemaker
from oslo_log import log


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


def get_node(node_name):
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


def disrupt_all_controller_nodes(disrupt_method=hard_reset_method,
                                 exclude_list=None):
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

    for controller in topology.list_openstack_nodes(group='controller'):
        controller_checked = sh.execute("hostname",
                                        ssh_client=controller.ssh_client,
                                        expect_exit_status=None).stdout
        LOG.info('{} is up '.format(controller_checked))


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
