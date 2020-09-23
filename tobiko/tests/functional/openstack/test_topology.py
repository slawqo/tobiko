# Copyright (c) 2019 Red Hat, Inc.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import absolute_import

import testtools

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import nova
from tobiko.openstack import topology
from tobiko.shell import ping
from tobiko.shell import sh


@keystone.skip_unless_has_keystone_credentials()
class OpenStackTopologyTest(testtools.TestCase):

    topology = tobiko.required_setup_fixture(topology.OpenStackTopology)

    def test_get_openstack_topology(self):
        topology_class = type(self.topology)
        topo = topology.get_openstack_topology(topology_class=topology_class)
        self.assertIs(topo, self.topology)
        self.assertIsInstance(topo, topology.OpenStackTopology)

    def test_ping_node(self):
        for node in self.topology.nodes:
            ping.ping(node.public_ip, count=1, timeout=5.).assert_replied()

    def test_ssh_client(self):
        for node in self.topology.nodes:
            self.assertIsNotNone(node.ssh_client)
            hostname = sh.get_hostname(
                ssh_client=node.ssh_client).split('.')[0]
            self.assertEqual(node.name, hostname)

    def test_controller_group(self):
        nodes = list(self.topology.get_group('controller'))
        self.assertNotEqual([], nodes)
        for node in nodes:
            self.assertIn('controller', node.groups)

    def test_compute_group(self):
        nodes = list(self.topology.get_group('compute'))
        self.assertNotEqual([], nodes)
        for node in nodes:
            self.assertIn('compute', node.groups)
        hypervisors = {
            hypervisor.hypervisor_hostname.split('.', 1)[0].lower(): hypervisor
            for hypervisor in nova.list_hypervisors()}
        for name, hypervisor in hypervisors.items():
            node = self.topology.get_node(name)
            self.assertEqual(name, node.name)
            self.assertIn(node, nodes)

    def test_list_openstack_topology(self, group=None, hostnames=None):
        nodes = topology.list_openstack_nodes(
            topology=self.topology, group=group, hostnames=hostnames)
        self.assertTrue(set(nodes).issubset(set(self.topology.nodes)))
        for node in nodes:
            if group:
                self.assertIn(group, node.groups)
            if hostnames:
                hostnames = [node_name_from_hostname(h)
                             for h in hostnames]
                self.assertIn(node.name, hostnames)
        return nodes

    def test_list_openstack_topology_with_group(self):
        self.test_list_openstack_topology(group='compute')

    def test_list_openstack_topology_with_hostnames(self):
        expected_nodes = self.topology.nodes[0::2]
        actual_nodes = self.test_list_openstack_topology(
            hostnames=[node.name for node in expected_nodes])
        self.assertEqual(expected_nodes, actual_nodes)


def node_name_from_hostname(hostname):
    return hostname.split('.', 1)[0].lower()
