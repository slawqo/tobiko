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

import netaddr
import testtools

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks


@keystone.skip_unless_has_keystone_credentials()
class PortTest(testtools.TestCase):

    #: Stack of resources with a network with a gateway router
    stack = tobiko.required_fixture(stacks.CirrosServerStackFixture)

    def test_get_port_with_id(self):
        return self._test_get_port(port=self.stack.port_id)

    def test_get_port_with_details(self):
        return self._test_get_port(port=self.stack.port_details)

    def _test_get_port(self, port: neutron.PortIdType):
        observed = neutron.get_port(port)
        port_id = neutron.get_port_id(port)
        self.assertEqual(port_id, observed['id'])

    def test_create_port(self,
                         network: neutron.NetworkIdType = None) \
            -> neutron.PortType:
        port = neutron.create_port(name=self.id(), network=network)
        self.assertIsInstance(port['id'], str)
        self.assertNotEqual('', port['id'])
        self.assertEqual(self.id(), port['name'])
        self.assertEqual(port['id'], neutron.get_port(port)['id'])
        if network is not None:
            self.assertEqual(neutron.get_network_id(network),
                             port['network_id'])
        return port

    def test_create_port_with_network_id(self):
        network = neutron.create_network()
        self.test_create_port(network=network['id'])

    def test_create_port_with_network_details(self):
        network = neutron.create_network()
        self.test_create_port(network=network)

    def test_delete_port_with_id(self):
        port = self.test_create_port()
        neutron.delete_port(port['id'])
        self.assertRaises(neutron.NoSuchPort, neutron.get_port,
                          port['id'])

    def test_delete_port_with_details(self):
        port = self.test_create_port()
        neutron.delete_port(port)
        self.assertRaises(neutron.NoSuchPort, neutron.get_port,
                          port['id'])

    def test_delete_network_with_invalid_id(self):
        self.assertRaises(neutron.NoSuchPort,
                          neutron.delete_port, '<invalid-id>')

    def test_list_port_addresses(self, ip_version=None):
        port = neutron.find_port(device_id=self.stack.server_id)
        port_addresses = neutron.list_port_ip_addresses(
            port=port,
            ip_version=ip_version)
        server_addresses = nova.list_server_ip_addresses(
            server=self.stack.server_details,
            ip_version=ip_version,
            address_type='fixed')
        self.assertEqual(set(server_addresses), set(port_addresses))
        if ip_version:
            self.assertEqual(
                port_addresses.with_attributes(version=ip_version),
                port_addresses)

    def test_list_port_addresses_with_ipv4(self):
        self.test_list_port_addresses(ip_version=4)

    def test_list_port_addresses_with_ipv6(self):
        self.test_list_port_addresses(ip_version=6)

    def test_find_port_address_with_ip_version(self):
        port = neutron.find_port(device_id=self.stack.server_id)
        server_addresses = nova.list_server_ip_addresses(
            server=self.stack.server_details,
            address_type='fixed')
        for server_address in server_addresses:
            port_address = neutron.find_port_ip_address(
                port=port,
                ip_version=server_address.version,
                unique=True)
            self.assertEqual(server_address, port_address)

    def test_find_port_address_with_subnet_id(self):
        port = neutron.find_port(device_id=self.stack.server_id)
        for subnet in neutron.list_subnets(network_id=port['network_id']):
            port_address = neutron.find_port_ip_address(
                port=port, subnet=subnet, unique=True)
            cidr = netaddr.IPNetwork(subnet['cidr'])
            self.assertIn(port_address, cidr)
