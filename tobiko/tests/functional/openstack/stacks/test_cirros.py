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
from tobiko.openstack import stacks
from tobiko.shell import ping
from tobiko.shell import sh


class CirrosServerStackTest(testtools.TestCase):
    """Tests connectivity to Nova instances via floating IPs"""

    #: Stack of resources with a server attached to a floating IP
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

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
