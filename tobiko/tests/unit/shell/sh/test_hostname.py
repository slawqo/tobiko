# Copyright (c) 2021 Red Hat, Inc.
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
from unittest import mock

import paramiko

from tobiko.shell import sh
from tobiko.shell import ssh
from tobiko.tests import unit


class HostnameTest(unit.TobikoUnitTest):

    def mock_ssh_client(self,
                        stdout='mocked-hostname\n',
                        stderr='',
                        exit_status=0) \
            -> ssh.SSHClientFixture:
        channel_mock = mock.MagicMock(spec=paramiko.Channel,
                                      exit_status=exit_status)
        channel_mock.recv.side_effect = [bytes(stdout, 'utf-8'),
                                         EOFError,
                                         EOFError] * 10
        channel_mock.recv_stderr.side_effect = [bytes(stderr, 'utf-8'),
                                                EOFError,
                                                EOFError] * 10

        client_mock = mock.MagicMock(spec=ssh.SSHClientFixture)
        client_mock.connect().get_transport().open_session.return_value = \
            channel_mock
        return client_mock

    def test_get_hostname_with_no_ssh_client(self):
        hostname = sh.get_hostname(ssh_client=False)
        self.assertEqual(socket.gethostname(), hostname)

    def test_get_hostname_with_ssh_client(self):
        ssh_client = self.mock_ssh_client()
        hostname = sh.get_hostname(ssh_client=ssh_client)
        self.assertEqual('mocked-hostname', hostname)
        self.assertIs(hostname,
                      sh.get_hostname(ssh_client=ssh_client))

    def test_get_hostname_with_no_cached(self):
        ssh_client = self.mock_ssh_client()
        hostname = sh.get_hostname(ssh_client=ssh_client,
                                   cached=False)
        self.assertEqual('mocked-hostname', hostname)
        self.assertIsNot(hostname,
                         sh.get_hostname(ssh_client=ssh_client,
                                         cached=False))

    def test_get_hostname_with_ssh_proxy(self):
        ssh_client = self.mock_ssh_client()
        self.patch(ssh, 'ssh_client_fixture', return_value=ssh_client)
        hostname = sh.get_hostname(ssh_client=None)
        self.assertEqual('mocked-hostname', hostname)

    def test_get_hostname_with_ssh_client_no_output(self):
        ssh_client = self.mock_ssh_client(stdout='\n')
        ex = self.assertRaises(sh.HostNameError,
                               sh.get_hostname,
                               ssh_client=ssh_client)
        self.assertIn('Invalid result', str(ex))

    def test_get_hostname_with_ssh_client_and_failure(self):
        ssh_client = self.mock_ssh_client(exit_status=1,
                                          stderr='command not found')
        ex = self.assertRaises(sh.HostNameError,
                               sh.get_hostname,
                               ssh_client=ssh_client)
        self.assertIn('command not found', str(ex))
