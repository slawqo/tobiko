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
import testtools

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.shell import ping
from tobiko.shell import sh


@keystone.skip_unless_has_keystone_credentials()
class CirrosServerStackTest(testtools.TestCase):
    """Tests connectivity to Nova instances via floating IPs"""

    #: Stack of resources with a server attached to a floating IP
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    nameservers_filenames: typing.Optional[typing.Sequence[str]] = None

    def test_ping(self):
        """Test connectivity to floating IP address"""
        ping.ping_until_received(
            self.stack.floating_ip_address).assert_replied()

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
        if self.stack.swap_maxsize is None:
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
        self._test_subnet_nameservers(
            subnet=self.stack.network_stack.ipv4_subnet_details,
            ip_version=4)

    def test_ipv6_subnet_nameservers(self):
        self._test_subnet_nameservers(
            subnet=self.stack.network_stack.ipv6_subnet_details,
            ip_version=6)

    def _test_subnet_nameservers(self, subnet, ip_version):
        subnet_nameservers = [netaddr.IPAddress(nameserver)
                              for nameserver in subnet['dns_nameservers']]
        if not subnet_nameservers:
            self.skipTest(f"Subnet '{subnet['id']}' has any IPv{ip_version} "
                          "nameserver")
        server_nameservers = sh.list_nameservers(
            ssh_client=self.stack.ssh_client, ip_version=ip_version,
            filenames=self.nameservers_filenames)
        self.assertEqual(subnet_nameservers, server_nameservers)

    def test_ping_ipv4_nameservers(self):
        self._test_ping_nameservers(ip_version=4)

    def test_ping_ipv6_nameservers(self):
        self._test_ping_nameservers(ip_version=6)

    @neutron.skip_unless_is_ovs()
    def _test_ping_nameservers(self, ip_version: int):
        nameservers = sh.list_nameservers(ssh_client=self.stack.ssh_client,
                                          filenames=self.nameservers_filenames,
                                          ip_version=ip_version)
        if not nameservers:
            self.skipTest(f"Target server has no IPv{ip_version} "
                          "nameservers configured")
        ping.assert_reachable_hosts(nameservers,
                                    ssh_client=self.stack.ssh_client,
                                    count=5)


class EvacuablesServerStackTest(CirrosServerStackTest):

    #: Stack of resources with a server attached to a floating IP
    stack = tobiko.required_setup_fixture(stacks.EvacuableServerStackFixture)

    def test_image_fixture_tags(self):
        image_fixture = self.stack.image_fixture
        self.assertEqual(['evacuable'], image_fixture.tags)

    def test_image_tags(self):
        image = self.stack.image_fixture.get_image()
        self.assertEqual(['evacuable'], image.tags)
