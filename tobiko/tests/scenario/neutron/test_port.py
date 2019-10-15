# Copyright (c) 2019 Red Hat
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
from tobiko.shell import ping
from tobiko.shell import ip
from tobiko.openstack import neutron
from tobiko.openstack import stacks


class PortTest(testtools.TestCase):
    """Test Neutron ports"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def test_port_ips(self):
        port = self.stack.port_details
        server_addresses = ip.list_ip_addresses(
            ssh_client=self.stack.ssh_client)
        for address in neutron.list_port_ip_addresses(port=port):
            self.assertIn(address, server_addresses)

    def test_port_network(self):
        port = self.stack.port_details
        self.assertEqual(self.stack.network_stack.network_id,
                         port['network_id'])

    def test_port_subnets(self):
        port_subnets = {fixed_ip['subnet_id']
                        for fixed_ip in self.stack.port_details['fixed_ips']}
        subnets = set(self.stack.network_stack.network_details['subnets'])
        self.assertEqual(port_subnets, subnets)

    def test_ping_subnet_gateways(self):
        subnet_ids = self.stack.network_stack.network_details['subnets']
        subnet_gateway_ips = [
            netaddr.IPAddress(neutron.get_subnet(subnet_id)['gateway_ip'])
            for subnet_id in subnet_ids]
        reachable_gateway_ips = [
            gateway_ip
            for gateway_ip in subnet_gateway_ips
            if ping.ping(gateway_ip,
                         ssh_client=self.stack.ssh_client).received]
        self.assertEqual(subnet_gateway_ips, reachable_gateway_ips)

    def test_ping_port(self, network_id=None, device_id=None):
        network_id = network_id or self.stack.network_stack.network_id
        device_id = device_id or self.stack.server_id
        ports = neutron.list_ports(network_id=network_id,
                                   device_id=device_id)
        for port in ports:
            self.assertEqual(network_id, port['network_id'])
            self.assertEqual(device_id, port['device_id'])
            for address in neutron.list_port_ip_addresses(port=port):
                ping.ping(host=address,
                          ssh_client=self.stack.ssh_client).assert_replied()

    def test_ping_inner_gateway_ip(self):
        if not self.stack.network_stack.has_gateway:
            self.skip('Server network has no gateway router')
        self.test_ping_port(device_id=self.stack.network_stack.gateway_id)

    def test_ping_outer_gateway_ip(self):
        if not self.stack.network_stack.has_gateway:
            self.skip('Server network has no gateway router')
        self.test_ping_port(
            device_id=self.stack.network_stack.gateway_id,
            network_id=self.stack.network_stack.gateway_network_id)


# --- Test la-h3 extension ----------------------------------------------------

@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class L3HAPortTest(PortTest):
    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.L3haServerStackFixture)
