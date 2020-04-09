
from __future__ import absolute_import

import tobiko
from tobiko.shell import sh
from tobiko.openstack import topology
from tobiko.tripleo import topology as tripleo_topology
from oslo_log import log


LOG = log.getLogger(__name__)


def reset_all_controller_nodes(hard_reset=False):

    # reboot all controllers and wait for ssh Up on them
    # hard reset is simultaneous while soft is sequential
    if hard_reset:
        reset_method = 'sudo chmod o+w /proc/sysrq-trigger;' \
                       'sudo echo b > /proc/sysrq-trigger'
    else:
        reset_method = 'sudo reboot'
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


def reset_all_compute_nodes(hard_reset=False):

    # reboot all computes and wait for ssh Up on them
    # hard reset is simultaneous while soft is sequential
    if hard_reset:
        reset_method = 'sudo chmod o+w /proc/sysrq-trigger;' \
                       'sudo echo b > /proc/sysrq-trigger'
    else:
        reset_method = 'sudo reboot'
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
