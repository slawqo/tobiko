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
from oslo_log import log
import testtools

import tobiko
from tobiko.shell import files
from tobiko.shell import ping
from tobiko.shell import ip
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.openstack import topology


LOG = log.getLogger(__name__)


class PortTest(testtools.TestCase):
    """Test Neutron ports"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def test_port_ips(self, ip_version=None):
        port = self.stack.port_details
        port_ips = tobiko.Selection()
        for subnet in neutron.list_subnets(
                network_id=self.stack.network_stack.network_id):
            if subnet['enable_dhcp']:
                port_ips += neutron.list_port_ip_addresses(
                    port=port, subnet_id=subnet['id'], ip_version=ip_version)
            else:
                LOG.warning(f"Subnet '{subnet['id']}' has "
                            f" enable_dhcp={subnet['enable_dhcp']}")
        if port_ips:
            server_ips = ip.list_ip_addresses(scope='global',
                                              ssh_client=self.stack.ssh_client)
            self.assertEqual(set(port_ips), set(port_ips) & set(server_ips))
        elif ip_version:
            self.skipTest(f"No port IPv{ip_version} addresses found")
        else:
            self.skipTest("No port IP addresses found")

    def test_port_network(self):
        self.assertEqual(self.stack.network_stack.network_id,
                         self.stack.port_details['network_id'])

    def test_port_subnets(self):
        port_subnets = [fixed_ip['subnet_id']
                        for fixed_ip in self.stack.port_details['fixed_ips']]
        network_subnets = self.stack.network_stack.network_details['subnets']
        self.assertEqual(set(network_subnets), set(port_subnets))

    def test_ping_subnet_gateways(self):
        network_id = self.stack.network_stack.network_id
        subnets = neutron.list_subnets(network_id=network_id)
        gateway_ips = [netaddr.IPAddress(subnet['gateway_ip'])
                       for subnet in subnets]
        ping.assert_reachable_hosts(gateway_ips,
                                    ssh_client=self.stack.ssh_client)

    def test_ping_port(self, network_id=None, device_id=None,
                       ip_version=None):
        network_id = network_id or self.stack.network_stack.network_id
        device_id = device_id or self.stack.server_id
        ports = neutron.list_ports(network_id=network_id,
                                   device_id=device_id)
        port_ips: tobiko.Selection[netaddr.IPAddress] = tobiko.Selection()
        for port in ports:
            self.assertEqual(network_id, port['network_id'])
            self.assertEqual(device_id, port['device_id'])
            port_ips.extend(neutron.list_port_ip_addresses(port=port))
        if ip_version is not None:
            port_ips = port_ips.with_attributes(version=ip_version)
        server_ips = ip.list_ip_addresses(scope='global',
                                          ssh_client=self.stack.ssh_client)
        # Remove IPs that hasn't been assigned to server
        port_ips = tobiko.Selection(set(port_ips) & set(server_ips))
        if port_ips:
            ping.assert_reachable_hosts(port_ips,
                                        ssh_client=self.stack.ssh_client)
        elif ip_version:
            self.skipTest(f"No port IPv{ip_version} addresses found")
        else:
            self.skipTest("No port IP addresses found")

    @tobiko.retry_test_case(interval=30.)
    def test_ping_inner_gateway_ip(self, ip_version=None):
        if not self.stack.network_stack.has_gateway:
            self.skip('Server network has no gateway router')
        self.test_ping_port(device_id=self.stack.network_stack.gateway_id,
                            ip_version=ip_version)


# --- Test opening ports on external network ----------------------------------

@stacks.skip_unless_has_external_network
class ExternalPortTest(PortTest):
    """Test Neutron ports"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(
        stacks.CirrosExternalServerStackFixture)


# --- Test la-h3 extension ----------------------------------------------------

@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class L3HAPortTest(PortTest):
    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.L3haServerStackFixture)


@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class CentosServerL3HAPortTestWith(PortTest):
    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.L3haCentosServerStackFixture)


@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class UbuntuServerL3HAPortTestWith(PortTest):
    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.L3haUbuntuServerStackFixture)


class PortLogsStack(stacks.CirrosServerStackFixture):
    pass


@neutron.skip_unless_is_ovs()
class PortLogs(testtools.TestCase):

    stack = tobiko.required_setup_fixture(PortLogsStack)

    LOG_FILENAME = '/var/log/containers/neutron/server.log*'

    def test_nova_port_notification(self):
        pattern = f'Nova.+event.+response.*{self.stack.server_id}'
        log_digger = files.MultihostLogFileDigger(filename=self.LOG_FILENAME,
                                                  sudo=True)
        for node in topology.list_openstack_nodes(group='controller'):
            log_digger.add_host(hostname=node.hostname,
                                ssh_client=node.ssh_client)
        log_digger.find_lines(pattern=pattern)

        nova.shutoff_server(self.stack.server_id)
        nova.activate_server(self.stack.server_id)

        new_lines = log_digger.find_new_lines(pattern=pattern)

        plugged_events = [
            (hostname, line)
            for hostname, line in new_lines
            if 'network-vif-plugged' in line and self.stack.port_id in line]
        self.assertEqual(1, len(plugged_events), new_lines)

        unplugged_events = [
            (hostname, line)
            for hostname, line in new_lines
            if 'network-vif-unplugged' in line and self.stack.port_id in line]
        self.assertEqual(1, len(unplugged_events), new_lines)
