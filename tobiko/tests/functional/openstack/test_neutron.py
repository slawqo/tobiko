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
        network = neutron.find_network(id=self.stack.network_id)
        self.assertEqual(self.stack.network_id, network['id'])

    def test_find_floating_network(self):
        floating_network = CONF.tobiko.neutron.floating_network
        if not floating_network:
            tobiko.skip('floating_network not configured')
        network = neutron.find_network(name=floating_network)
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

    def test_get_network(self):
        network = neutron.get_network(self.stack.network_id)
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

    def test_get_router(self):
        if not self.stack.has_gateway:
            tobiko.skip("Stack {stack} has no gateway router",
                        stack=self.stack.stack_name)
        router = neutron.get_router(self.stack.gateway_id)
        self.assertEqual(self.stack.gateway_id, router['id'])

    def test_get_ipv4_subnet(self):
        if not self.stack.has_ipv4:
            tobiko.skip("Stack {stack} has no IPv4 subnet",
                        stack=self.stack.stack_name)
        subnet = neutron.get_subnet(self.stack.ipv4_subnet_id)
        self.assertEqual(self.stack.ipv4_subnet_id, subnet['id'])
        self.assertEqual(self.stack.ipv4_subnet_details, subnet)

    def test_get_ipv6_subnet(self):
        if not self.stack.has_ipv6:
            tobiko.skip("Stack {stack} has no IPv6 subnet",
                        stack=self.stack.stack_name)
        subnet = neutron.get_subnet(self.stack.ipv6_subnet_id)
        self.assertEqual(self.stack.ipv6_subnet_id, subnet['id'])
        self.assertEqual(self.stack.ipv6_subnet_details, subnet)

    def test_find_agents_with_binary_id(self):
        agents = neutron.list_agents(binary='neutron-l3-agent')
        self.assertTrue(agents)


class AgentTest(testtools.TestCase):

    def test_skip_if_missing_agents(self, count=1, should_skip=False,
                                    **params):
        if should_skip:
            expected_exeption = self.skipException
        else:
            expected_exeption = self.failureException

        @neutron.skip_if_missing_networking_agents(count=count, **params)
        def method():
            raise self.fail('Not skipped')

        exception = self.assertRaises(expected_exeption, method)
        if should_skip:
            agents = neutron.list_agents(**params)
            message = "missing {!r} agent(s)".format(count - len(agents))
            if params:
                message += " with {!s}".format(
                    ','.join('{!s}={!r}'.format(k, v)
                             for k, v in params.items()))
            self.assertEqual(message, str(exception))
        else:
            self.assertEqual('Not skipped', str(exception))

    def test_skip_if_missing_agents_with_no_agents(self):
        self.test_skip_if_missing_agents(binary='never-never-land',
                                         should_skip=True)

    def test_skip_if_missing_agents_with_big_count(self):
        self.test_skip_if_missing_agents(count=1000000,
                                         should_skip=True)
