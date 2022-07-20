# Copyright 2022 Red Hat
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
from tobiko import shiftstack


@shiftstack.skip_unless_has_shiftstack()
class ShiftstackNeutronTest(testtools.TestCase):

    def test_list_shiftstack_node_ip_addresses(self):
        server = shiftstack.find_shiftstack_node(status='ACTIVE')
        addresses = shiftstack.list_shiftstack_node_ip_addresses(server=server)
        self.assertIsInstance(addresses, tobiko.Selection)
        self.assertNotEqual([], addresses)
        return addresses

    def test_find_shiftstack_node_ip_address(self):
        server = shiftstack.find_shiftstack_node(status='ACTIVE')
        address = shiftstack.find_shiftstack_node_ip_address(server=server)
        self.assertIsInstance(address, netaddr.IPAddress)
        self.assertEqual(
            address,
            shiftstack.list_shiftstack_node_ip_addresses(server=server).first)
