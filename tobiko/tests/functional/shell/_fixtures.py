from __future__ import absolute_import

import testtools
from oslo_log import log

import tobiko
from tobiko.openstack import topology
from tobiko.shell import ip
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


class NetworkNamespaceFixture(tobiko.SharedFixture):

    def __init__(self,
                 network_namespace: str = None,
                 ssh_client: ssh.SSHClientType = None):
        super().__init__()
        self.network_namespace = network_namespace
        self.ssh_client = ssh_client

    def setup_fixture(self):
        errors = []
        for node in topology.list_openstack_nodes():
            try:
                namespace: str = ip.list_network_namespaces(
                    ignore_errors=True,
                    ssh_client=node.ssh_client).first
            except tobiko.ObjectNotFound:
                LOG.debug(f'No such namespace on host {node.name}',
                          exc_info=1)
            except Exception:
                LOG.debug(f'Error listing namespace on host {node.name}',
                          exc_info=1)
                errors.append(tobiko.exc_info())
            else:
                self.network_namespace = namespace
                self.ssh_client = node.ssh_client
                break
        else:
            if errors:
                raise testtools.MultipleExceptions(*errors)
            else:
                tobiko.skip_test(reason='Network namespace not found')
