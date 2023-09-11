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

import typing

import netaddr
import pytest
import testtools

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.shell import ping
from tobiko.shell import sh


@keystone.skip_unless_has_keystone_credentials()
class CirrosServerStackTest(testtools.TestCase):
    """Tests connectivity to Nova instances via floating IPs"""

    #: Stack of resources with a server attached to a floating IP
    stack = tobiko.required_fixture(stacks.CirrosServerStackFixture)

    nameservers_filenames: typing.Optional[typing.Sequence[str]] = None

    @property
    def peer_ssh_client(self):
        return self.stack.ssh_client

    def test_ping_floating_ip(self):
        """Test connectivity to floating IP address"""
        ping.assert_reachable_hosts([self.stack.floating_ip_address])

    def test_ping_fixed_ipv4(self):
        ping.assert_reachable_hosts([self.get_fixed_ip(ip_version=4)],
                                    ssh_client=self.peer_ssh_client)

    def test_ping_fixed_ipv6(self):
        ping.assert_reachable_hosts([self.get_fixed_ip(ip_version=6)],
                                    ssh_client=self.peer_ssh_client)

    def get_fixed_ip(self, ip_version: int):
        try:
            return self.stack.find_fixed_ip(ip_version=ip_version)
        except tobiko.ObjectNotFound:
            self.skipTest(f"Server {self.stack.server_id} has any "
                          f"IPv{ip_version} address.")

    def test_ssh_connect(self):
        """Test SSH connectivity via Paramiko SSHClient"""
        self.stack.ssh_client.connect()

    def test_hostname(self):
        """Test that hostname of instance server matches Nova server name"""
        self.stack.ssh_client.connect()

        stdout = sh.execute('hostname',
                            ssh_client=self.stack.ssh_client).stdout
        hostname = stdout.strip().split('.', 1)[0]
        self.assertEqual(self.stack.server_name, hostname)

    def test_console_output(self):
        # wait for server to be ready for connection
        self.stack.ssh_client.connect()
        output = self.stack.console_output
        self.assertTrue(output)

    def test_swap_file(self):
        if getattr(self.stack, 'swap_maxsize', None) is None:
            self.skipTest('Swap maxsize is None')

        cloud_config = self.stack.cloud_config
        self.assertEqual({'filename': self.stack.swap_filename,
                          'size': self.stack.swap_size or "auto",
                          'maxsize': self.stack.swap_maxsize},
                         cloud_config['swap'])

        nova.wait_for_cloud_init_done(ssh_client=self.stack.ssh_client)
        # check swap file exists
        sh.execute(f"ls -lh '{self.stack.swap_filename}'",
                   ssh_client=self.stack.ssh_client)
        # check swap file is mounted
        swaps_table = sh.execute("cat /proc/swaps",
                                 ssh_client=self.stack.ssh_client).stdout
        mounted_filenames = [line.split()[0]
                             for line in swaps_table.splitlines()[1:]]
        self.assertIn(self.stack.swap_filename, mounted_filenames, swaps_table)

    def test_ipv4_subnet_nameservers(self):
        self._test_subnet_nameservers(ip_version=4)

    def test_ipv6_subnet_nameservers(self):
        self._test_subnet_nameservers(ip_version=6)

    def _test_subnet_nameservers(self, ip_version):
        def get_subnet_nameservers(network_stack, ip_version):
            # returns a tuple with:
            # 1. the subnet name (str)
            # 2. the subnet dns nameservers (list of str)
            subnet_details = (network_stack.ipv4_subnet_details
                              if ip_version == 4
                              else network_stack.ipv6_subnet_details)
            nameservers = [netaddr.IPAddress(nameserver)
                           for nameserver in subnet_details['dns_nameservers']]
            return (subnet_details['name'], nameservers)

        subnet_name, subnet_nameservers = get_subnet_nameservers(
            self.stack.network_stack, ip_version)

        if self.stack.has_vlan:
            vlan_subnet_name, vlan_subnet_nameservers = get_subnet_nameservers(
                self.stack.vlan_network_stack, ip_version)
            subnet_names = ','.join([subnet_name, vlan_subnet_name])
            subnet_nameservers += vlan_subnet_nameservers
        else:
            subnet_names = subnet_name

        if not subnet_nameservers:
            self.skipTest(f"Subnet(s) '{subnet_names}' have no IPv{ip_version}"
                          " nameservers")
        server_nameservers = sh.list_nameservers(
            ssh_client=self.stack.ssh_client, ip_version=ip_version,
            filenames=self.nameservers_filenames)
        self.assertEqual(subnet_nameservers, server_nameservers)


class EvacuablesServerStackTest(CirrosServerStackTest):

    #: Stack of resources with a server attached to a floating IP
    stack = tobiko.required_fixture(stacks.EvacuableServerStackFixture)

    def test_image_fixture_tags(self):
        image_fixture = self.stack.image_fixture
        self.assertEqual(['evacuable'], image_fixture.tags)

    def test_image_tags(self):
        image = self.stack.image_fixture.get_image()
        self.assertEqual(['evacuable'], image.tags)


@pytest.mark.flaky(reruns=2, reruns_delay=60)
class CirrosPeerServerStackTest(CirrosServerStackTest):

    #: Stack of resources with an HTTP server
    stack = tobiko.required_fixture(stacks.CirrosPeerServerStackFixture)

    @property
    def peer_ssh_client(self):
        return self.stack.peer_stack.ssh_client

    def test_ping_floating_ip(self):
        self.skipTest(f"Server '{self.stack.server_id}' has any floating IP")
