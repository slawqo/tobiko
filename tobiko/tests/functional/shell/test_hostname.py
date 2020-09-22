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

import socket

import six
import testtools

import tobiko
from tobiko.shell import sh
from tobiko.shell import ssh
from tobiko.openstack import keystone
from tobiko.openstack import stacks


@keystone.skip_unless_has_keystone_credentials()
class HostnameTest(testtools.TestCase):

    server_stack = tobiko.required_setup_fixture(
        stacks.CirrosServerStackFixture)

    def test_hostname(self, expect_hostname=None, **execute_params):
        hostname = sh.get_hostname(**execute_params)
        self.assertIsInstance(hostname, six.string_types)
        if expect_hostname:
            self.assertEqual(expect_hostname, hostname)
        else:
            self.assertNotEqual('', hostname)

    def test_local_hostname(self):
        self.test_hostname(expect_hostname=socket.gethostname(),
                           ssh_client=False)

    def test_remote_hostname(self, ssh_client=None):
        ssh_client = ssh_client or self.server_stack.ssh_client
        stdin, stdput, stderr = ssh_client.connect().exec_command('hostname')
        stdin.close()
        self.assertEqual(b'', stderr.read())
        self.test_hostname(ssh_client=ssh_client,
                           expect_hostname=stdput.read().decode().strip())

    def test_proxy_hostname(self):
        ssh_client = ssh.ssh_proxy_client()
        if ssh_client is None:
            self.skip('SSH proxy server not configured')
        self.test_remote_hostname(ssh_client=ssh_client)
