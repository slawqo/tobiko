# Copyright (c) 2022 Red Hat, Inc.
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
from tobiko import config
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import stacks


CONF = config.CONF


@keystone.skip_unless_has_keystone_credentials()
class NetworkTest(testtools.TestCase):
    """Tests network creation"""

    #: Stack of resources with a network with a gateway router
    stack = tobiko.required_fixture(stacks.NetworkStackFixture)

    def test_find_network_with_id(self):
        network = neutron.find_network(id=self.stack.network_id)
        self.assertEqual(self.stack.network_id, network['id'])

    def test_list_networks(self):
        networks = neutron.list_networks()
        network_ids = {n['id'] for n in networks}
        self.assertIn(self.stack.network_id, network_ids)

    def test_get_network_with_id(self):
        return self._test_get_network(network=self.stack.network_id)

    def test_get_network_with_details(self):
        return self._test_get_network(network=self.stack.network_details)

    def _test_get_network(self, network: neutron.NetworkIdType):
        observed = neutron.get_network(network)
        network_id = neutron.get_network_id(network)
        self.assertEqual(network_id, observed['id'])

    def test_create_network(self) -> neutron.NetworkType:
        network = neutron.create_network(name=self.id())
        self.assertIsInstance(network['id'], str)
        self.assertNotEqual('', network['id'])
        self.assertEqual(self.id(), network['name'])
        self.assertEqual(network['id'], neutron.get_network(network)['id'])
        return network

    def test_delete_network_with_id(self):
        network = self.test_create_network()
        neutron.delete_network(network['id'])
        self.assertRaises(neutron.NoSuchNetwork, neutron.get_network,
                          network['id'])

    def test_delete_network_with_details(self):
        network = self.test_create_network()
        neutron.delete_network(network)
        self.assertRaises(neutron.NoSuchNetwork, neutron.get_network,
                          network['id'])

    def test_delete_network_with_invalid_id(self):
        self.assertRaises(neutron.NoSuchNetwork,
                          neutron.delete_network, '<invalid-id>')

    def test_network_stack(self):
        network = neutron.get_network(self.stack.network_id)
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
