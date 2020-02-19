from __future__ import absolute_import

import tobiko
from tobiko.openstack import topology
from tobiko.shell import ip


class NetworkNamespaceFixture(tobiko.SharedFixture):

    network_namespace = None
    ssh_client = None

    def setup_fixture(self):
        for node in topology.list_openstack_nodes():
            network_namespaces = ip.list_network_namespaces(
                ignore_errors=True,
                ssh_client=node.ssh_client)
            if network_namespaces:
                self.network_namespace = network_namespaces.first
                self.ssh_client = node.ssh_client
