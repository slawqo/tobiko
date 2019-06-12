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
from tobiko import config
from tobiko.openstack import neutron
from tobiko.openstack import stacks


CONF = config.CONF


class NeutronApiTestCase(testtools.TestCase):
    """Tests network creation"""

    #: Stack of resources with a network with a gateway router
    stack = tobiko.required_setup_fixture(stacks.NetworkStackFixture)

    def test_find_network_with_id(self):
        network = neutron.find_network(self.stack.network_id)
        self.assertEqual(self.stack.network_id, network['id'])

    def test_find_floating_network(self):
        floating_network = CONF.tobiko.neutron.floating_network
        if not floating_network:
            tobiko.skip('floating_network not configured')
        network = neutron.find_network(floating_network)
        self.assertIn(floating_network, [network['name'], network['id']])
        self.assertEqual(self.stack.gateway_network_id, network['id'])

    def test_list_networks(self):
        networks = neutron.list_networks()
        network_ids = {n['id'] for n in networks}
        self.assertIn(self.stack.network_id, network_ids)

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

    def test_show_network(self):
        network = neutron.show_network(self.stack.network_id)
        self.assertEqual(self.stack.network_id, network['id'])
        self.assertEqual(self.stack.port_security_enabled,
                         network['port_security_enabled'])
        if self.stack.has_ipv4:
            self.assertIn(self.stack.ipv4_subnet_id, network['subnets'])
        else:
            self.assertNotIn(self.stack.ipv4_subnet_id, network['subnets'])
        if self.stack.has_ipv6:
            self.assertIn(self.stack.ipv6_subnet_id, network['subnets'])
        else:
            self.assertNotIn(self.stack.ipv6_subnet_id, network['subnets'])

    def test_show_router(self):
        if not self.stack.has_gateway:
            tobiko.skip("Stack {stack} has no gateway router",
                        stack=self.stack.stack_name)
        router = neutron.show_router(self.stack.gateway_id)
        self.assertEqual(self.stack.gateway_id, router['id'])

    def test_show_ipv4_subnet(self):
        if not self.stack.has_ipv4:
            tobiko.skip("Stack {stack} has no IPv4 subnet",
                        stack=self.stack.stack_name)
        subnet = neutron.show_subnet(self.stack.ipv4_subnet_id)
        self.assertEqual(self.stack.ipv4_subnet_id, subnet['id'])
        self.assertEqual(str(self.stack.ipv4_cidr), subnet['cidr'])

    def test_show_ipv6_subnet(self):
        if not self.stack.has_ipv6:
            tobiko.skip("Stack {stack} has no IPv6 subnet",
                        stack=self.stack.stack_name)
        subnet = neutron.show_subnet(self.stack.ipv6_subnet_id)
        self.assertEqual(self.stack.ipv6_subnet_id, subnet['id'])
        self.assertEqual(str(self.stack.ipv6_cidr), subnet['cidr'])
