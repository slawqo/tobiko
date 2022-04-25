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
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import stacks


@keystone.skip_unless_has_keystone_credentials()
class FloatingIpTest(testtools.TestCase):

    server = tobiko.required_fixture(stacks.CirrosServerStackFixture)

    @property
    def floating_network_id(self) -> str:
        return stacks.get_floating_network_id()

    @property
    def floating_network_details(self) -> neutron.NetworkType:
        return stacks.get_floating_network()

    def test_create_floating_ip(self,
                                network: neutron.NetworkIdType = None) -> \
            neutron.FloatingIpType:
        floating_ip = neutron.create_floating_ip(network=network)
        self.assertIsInstance(floating_ip, dict)
        if network is None:
            floating_network_id = self.floating_network_id
        else:
            floating_network_id = neutron.get_network_id(network)
        self.assertEqual(floating_network_id,
                         floating_ip['floating_network_id'])
        self.assertEqual(floating_ip, neutron.get_floating_ip(floating_ip))
        return floating_ip

    def test_create_floating_ip_with_network_id(self):
        self.test_create_floating_ip(network=self.floating_network_id)

    def test_create_floating_ip_with_network_details(self):
        self.test_create_floating_ip(network=self.floating_network_details)

    def test_delete_floating_ip_with_id(self):
        floating_ip = self.test_create_floating_ip()
        neutron.delete_floating_ip(floating_ip['id'])
        self.assertRaises(neutron.NoSuchFloatingIp,
                          neutron.get_floating_ip, floating_ip)

    def test_delete_floating_ip_with_details(self):
        floating_ip = self.test_create_floating_ip()
        neutron.delete_floating_ip(floating_ip)
        self.assertRaises(neutron.NoSuchFloatingIp,
                          neutron.get_floating_ip, floating_ip)

    def test_delete_floating_ip_with_invalid_id(self):
        self.assertRaises(neutron.NoSuchFloatingIp,
                          neutron.delete_floating_ip, '<invalid-id>')

    def test_list_floating_ips(self):
        port_id = self.server.port_id
        floating_ips = neutron.list_floating_ips()
        floating_ip = floating_ips.with_items(port_id=port_id).unique
        self.assertEqual(floating_ip['floating_ip_address'],
                         self.server.floating_ip_address)

    def test_list_floating_ip_with_port_id(self):
        port_id = self.server.port_id
        floating_ip = neutron.list_floating_ips(port_id=port_id).unique
        self.assertEqual(floating_ip['floating_ip_address'],
                         self.server.floating_ip_address)

    def test_list_floating_ip_with_floating_ip_address(self):
        floating_ip_address = self.server.floating_ip_address
        floating_ip = neutron.list_floating_ips(
            floating_ip_address=floating_ip_address).unique
        self.assertEqual(floating_ip['port_id'],
                         self.server.port_id)

    def test_find_floating_ip_with_port_id(self):
        port_id = self.server.port_id
        floating_ip = neutron.find_floating_ip(port_id=port_id, unique=True)
        self.assertEqual(floating_ip['floating_ip_address'],
                         self.server.floating_ip_address)

    def test_find_floating_ip_with_floating_ip_address(self):
        floating_ip_address = self.server.floating_ip_address
        floating_ip = neutron.find_floating_ip(
            floating_ip_address=floating_ip_address)
        self.assertEqual(floating_ip, self.server.floating_ip_details)

    def test_find_floating_ip_with_invalid_floating_ip_address(self):
        self.assertRaises(tobiko.ObjectNotFound,
                          neutron.find_floating_ip,
                          floating_ip_address='1.2.3.4')
