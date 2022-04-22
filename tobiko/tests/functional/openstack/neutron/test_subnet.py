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
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import stacks


@keystone.skip_unless_has_keystone_credentials()
class SubnetTest(testtools.TestCase):
    """Tests network creation"""

    #: Stack of resources with a network with a gateway router
    stack = tobiko.required_fixture(stacks.NetworkStackFixture)

    def test_list_subnets(self):
        subnets = neutron.list_subnets()
        subnets_ids = {s['id'] for s in subnets}
        if self.stack.has_ipv4:
            self.assertIn(self.stack.ipv4_subnet_id, subnets_ids)
        if self.stack.has_ipv6:
            self.assertIn(self.stack.ipv6_subnet_id, subnets_ids)

    def test_list_subnet_cidrs(self):
        subnets_cidrs = neutron.list_subnet_cidrs()
        if self.stack.has_ipv4:
            cidr = netaddr.IPNetwork(self.stack.ipv4_subnet_details['cidr'])
            self.assertIn(cidr, subnets_cidrs)
        if self.stack.has_ipv6:
            cidr = netaddr.IPNetwork(self.stack.ipv6_subnet_details['cidr'])
            self.assertIn(cidr, subnets_cidrs)

    def test_get_ipv4_subnet(self):
        if not self.stack.has_ipv4:
            tobiko.skip_test(
                "Stack {self.stack.stack_name} has no IPv4 subnet")
        subnet = neutron.get_subnet(self.stack.ipv4_subnet_id)
        self.assertEqual(self.stack.ipv4_subnet_id, subnet['id'])
        self.assertEqual(self.stack.ipv4_subnet_details, subnet)

    def test_get_ipv6_subnet(self):
        if not self.stack.has_ipv6:
            tobiko.skip_test(
                "Stack {self.stack.stack_name} has no IPv6 subnet")
        subnet = neutron.get_subnet(self.stack.ipv6_subnet_id)
        self.assertEqual(self.stack.ipv6_subnet_id, subnet['id'])
        self.assertEqual(self.stack.ipv6_subnet_details, subnet)

    def test_create_subnet(self):
        network = neutron.create_network(name=self.id())
        cidr = neutron.new_ipv4_cidr()
        subnet = neutron.create_subnet(network=network,
                                       ip_version=4,
                                       cidr=cidr)
        self.assertEqual(network['id'], subnet['network_id'])
        self.assertEqual(str(cidr), subnet['cidr'])
        self.assertEqual(subnet['id'], neutron.get_subnet(subnet=subnet)['id'])
        return subnet

    def test_delete_subnet_with_id(self):
        subnet = self.test_create_subnet()
        neutron.delete_subnet(subnet['id'])
        self.assertRaises(neutron.NoSuchSubnet,
                          neutron.get_subnet, subnet=subnet['id'])

    def test_delete_subnet_with_details(self):
        subnet = self.test_create_subnet()
        neutron.delete_subnet(subnet)
        self.assertRaises(neutron.NoSuchSubnet,
                          neutron.get_subnet, subnet=subnet)

    def test_delete_subnet_with_invalid_id(self):
        self.assertRaises(neutron.NoSuchSubnet, neutron.delete_subnet,
                          '<invalid-id>')
