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

import netaddr

import testtools

import tobiko
from tobiko.openstack import nova
from tobiko.openstack import topology
from tobiko.shell import ping
from tobiko.shell import sh


class OpenStackTopologyTest(testtools.TestCase):

    topology = tobiko.required_setup_fixture(topology.OpenStackTopology)

    def test_get_openstack_topology(self):
        topology_class = type(self.topology)
        topo = topology.get_openstack_topology(topology_class=topology_class)
        self.assertIsInstance(topo, topology.OpenStackTopology)
        self.assertNotEqual([], list(topo.nodes))
        self.assertNotEqual([], list(topo.groups))

    def test_ping_node(self):
        topo = topology.get_openstack_topology()
        for node in topo.nodes:
            for address in node.addresses:
                ping.ping(address, count=1).assert_replied()

    def test_ssh_client(self):
        for node in self.topology.nodes:
            hostname = sh.get_hostname(
                ssh_client=node.ssh_client).split('.')[0]
            self.assertEqual(node.name, hostname)

    def test_compute_group(self):
        group = self.topology.get_group('compute')
        nodes = group.nodes
        hypervisors = {hypervisor.hypervisor_hostname.split('.')[0]: hypervisor
                       for hypervisor in nova.list_hypervisors()}
        self.assertEqual(sorted(hypervisors),
                         sorted([node.name for node in nodes]))
        for name, hypervisor in hypervisors.items():
            node = self.topology.get_node(name)
            self.assertEqual(name, node.name)
            if ping.ping(hypervisor.host_ip).received:
                self.assertIn(netaddr.IPAddress(hypervisor.host_ip),
                              node.addresses)
            self.assertIn(group, node.groups)
