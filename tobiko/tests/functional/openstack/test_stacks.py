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

import testtools

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import stacks
from tobiko.shell import ping
from tobiko.shell import sh


class NetworkTestCase(testtools.TestCase):
    """Tests network creation"""

    #: Stack of resources with a server attached to a floating IP
    stack = tobiko.required_setup_fixture(stacks.NetworkStackFixture)

    @property
    def network_details(self):
        return neutron.get_neutron_client().show_network(
            self.stack.network_id)['network']

    @neutron.skip_if_missing_networking_extensions('port-security')
    def test_port_security_enabled(self):
        port_security_enabled = self.stack.port_security_enabled
        self.assertEqual(port_security_enabled,
                         self.network_details['port_security_enabled'])
        self.assertEqual(port_security_enabled,
                         self.stack.outputs.port_security_enabled)

    @neutron.skip_if_missing_networking_extensions('net-mtu')
    def test_net_mtu(self):
        self.assertEqual(self.network_details['mtu'], self.stack.outputs.mtu)

    @neutron.skip_if_missing_networking_extensions('net-mtu-write')
    def test_net_mtu_write(self):
        self.assertEqual(self.stack.mtu, self.stack.outputs.mtu)


class FloatingIpServerTest(testtools.TestCase):
    """Tests connectivity to Nova instances via floating IPs"""

    #: Stack of resources with a server attached to a floating IP
    stack = tobiko.required_setup_fixture(stacks.FloatingIpServerStackFixture)

    def test_ping(self):
        """Test connectivity to floating IP address"""
        ping.ping_until_received(
            self.stack.floating_ip_address).assert_replied()

    def test_ssh_connect(self):
        """Test SSH connectivity via Paramiko SSHClient"""
        self.stack.ssh_client.connect()

    def test_ssh_command(self):
        """Test SSH connectivity via OpenSSH client"""
        sh.execute('true', shell=self.stack.ssh_command)

    def test_hostname(self):
        """Test that hostname of instance server matches Nova server name"""
        result = sh.execute('hostname', ssh_client=self.stack.ssh_client)
        hostname, = str(result.stdout).splitlines()
        self.assertEqual(hostname, self.stack.server_name)
