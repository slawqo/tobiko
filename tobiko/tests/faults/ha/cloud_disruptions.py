
from __future__ import absolute_import

import tobiko
from tobiko.shell import sh
from tobiko.openstack import topology
from oslo_log import log


LOG = log.getLogger(__name__)


def reset_all_controller_nodes_sequentially():

    # reboot all controllers and wait for ssh Up on them
    nodes = topology.list_openstack_nodes(group='controller')
    for controller in nodes:
        sh.execute("sudo reboot", ssh_client=controller.ssh_client,
                   expect_exit_status=None)
        LOG.info('rebooted {}'.format(controller.name))
        tobiko.cleanup_fixture(controller.ssh_client)

    for controller in topology.list_openstack_nodes(group='controller'):
        controller_checked = sh.execute("hostname",
                                        ssh_client=controller.ssh_client,
                                        expect_exit_status=None).stdout
        LOG.info('{} is up '.format(controller_checked))
