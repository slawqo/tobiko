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

import typing

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

    def test_port_ips(self, ip_version: typing.Optional[int] = None):
        """Checks port IPS has been assigned to server via DHCP protocol"""
        device_ips = set(neutron.list_device_ip_addresses(
            device_id=self.stack.server_id,
            network_id=self.stack.network_stack.network_id,
            enable_dhcp=True,
            ip_version=ip_version))
        if device_ips:
            server_ips = set(ip.list_ip_addresses(
                scope='global', ssh_client=self.stack.ssh_client))
            self.assertEqual(device_ips, device_ips & server_ips)
        elif ip_version:
            self.skipTest(f"No port IPv{ip_version} addresses found")
        else:
            self.skipTest("No port IP addresses found")

    def test_port_network(self):
        self.assertEqual(self.stack.network_stack.network_id,
                         self.stack.port_details['network_id'])

    def test_port_subnets(self):
        """Checks port subnets"""
        port_subnets = [fixed_ip['subnet_id']
                        for fixed_ip in self.stack.port_details['fixed_ips']]
        network_subnets = self.stack.network_stack.network_details['subnets']
        self.assertEqual(set(network_subnets), set(port_subnets))

    def test_ping_subnet_gateways(self):
        """Checks server can ping its gateway IPs"""
        network_id = self.stack.network_stack.network_id
        subnets = neutron.list_subnets(network_id=network_id,
                                       enable_dhcp=True)
        LOG.debug(f"Subnets with DHCP enabled are: {subnets}")
        gateway_ips = [netaddr.IPAddress(subnet['gateway_ip'])
                       for subnet in subnets]
        LOG.debug(f"Gateway IPs are: {gateway_ips}")
        ping.assert_reachable_hosts(gateway_ips,
                                    ssh_client=self.stack.ssh_client)

    def test_ping_port(self, network_id=None, device_id=None, ip_version=None):
        """Checks server can ping its own port"""
        device_ips = neutron.list_device_ip_addresses(
            device_id=device_id or self.stack.server_id,
            network_id=network_id or self.stack.network_stack.network_id,
            enable_dhcp=True, ip_version=ip_version)
        server_ips = ip.list_ip_addresses(scope='global',
                                          ssh_client=self.stack.ssh_client)
        # Remove IPs that hasn't been assigned to server
        port_ips = tobiko.Selection(set(device_ips) & set(server_ips))
        if port_ips:
            ping.assert_reachable_hosts(port_ips,
                                        ssh_client=self.stack.ssh_client)
        elif ip_version:
            self.skipTest(f"No port IPv{ip_version} addresses found")
        else:
            self.skipTest("No port IP addresses found")


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
class CentosServerL3HAPortTest(PortTest):
    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.L3haCentosServerStackFixture)


@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class UbuntuServerL3HAPortTest(PortTest):
    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.L3haUbuntuServerStackFixture)


# --- Port events logging ----------------------------------------------------

class PortLogsStack(stacks.CirrosServerStackFixture):
    pass


@neutron.skip_unless_is_ovs()
class PortLogsTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(PortLogsStack)

    def setUp(self):
        super(PortLogsTest, self).setUp()
        os_topology = topology.get_openstack_topology()
        self.LOG_FILENAME = os_topology.log_names_mappings[neutron.SERVER]
        self.FILE_DIGGER_CLASS = os_topology.file_digger_class

    def test_nova_port_notification(self):
        pattern = f'Nova.+event.+response.*{self.stack.server_id}'
        log_digger = files.MultihostLogFileDigger(
            filename=self.LOG_FILENAME,
            file_digger_class=self.FILE_DIGGER_CLASS,
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
