
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


def get_node(node_name):
    return [node for node in topology.list_openstack_nodes() if
            node.name == node_name][0]


def reset_node(node_name, hard_reset=False):

    # reboot all controllers and wait for ssh Up on them
    # hard reset is simultaneous while soft is sequential
    if hard_reset:
        reset_method = hard_reset_method
    else:
        reset_method = soft_reset_method

    # using ssh_client.connect we use a fire and forget reboot method
    node = get_node(node_name)
    node.ssh_client.connect().exec_command(reset_method)
    LOG.info('reboot exec: {} on server: {}'.format(reset_method,
                                                    node.name))
    tobiko.cleanup_fixture(node.ssh_client)

    node_checked = sh.execute("hostname",
                              ssh_client=node.ssh_client,
                              expect_exit_status=None).stdout
    LOG.info('{} is up '.format(node_checked))


def reset_all_controller_nodes(hard_reset=False):

    # reboot all controllers and wait for ssh Up on them
    # hard reset is simultaneous while soft is sequential
    if hard_reset:
        reset_method = hard_reset_method
    else:
        reset_method = soft_reset_method
    controlplane_groups = ['controller', 'messaging', 'database', 'networker']
    actual_controlplane_groups = tripleo_topology.actual_node_groups(
        controlplane_groups)
    nodes = topology.list_openstack_nodes(group=actual_controlplane_groups)
    for controller in nodes:
        # using ssh_client.connect we use a fire and forget reboot method
        controller.ssh_client.connect().exec_command(reset_method)
        LOG.info('reboot exec: {} on server: {}'.format(reset_method,
                                                        controller.name))
        tobiko.cleanup_fixture(controller.ssh_client)

    for controller in topology.list_openstack_nodes(group='controller'):
        controller_checked = sh.execute("hostname",
                                        ssh_client=controller.ssh_client,
                                        expect_exit_status=None).stdout
        LOG.info('{} is up '.format(controller_checked))


def reset_controller_main_vip(hard_reset=True):

    # reset the controller holding the main vip (os_auth_url)
    # ip resource (managed via pacemaker)
    # find main vip by getting it from
    credentials = keystone.default_keystone_credentials()
    auth_url = credentials.auth_url
    auth_url_ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', auth_url)[0]

    # find the node holding that resource via :
    main_vim_controller = pacemaker.get_overcloud_nodes_running_pcs_resource(
        resource=f"ip-{auth_url_ip}")[0]
    # get that node's ssh_client and reset it
    reset_node(main_vim_controller, hard_reset=hard_reset)


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
