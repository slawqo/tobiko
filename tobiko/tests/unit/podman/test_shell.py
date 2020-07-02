# Copyright 2018 Red Hat
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

import mock

from tobiko import podman
from tobiko.tests import unit


class TestShell(unit.TobikoUnitTest):

    @mock.patch('tobiko.shell.sh.execute')
    def test_discover_podman_socket(self, mock_execute):
        class FakeProcess:
            exit_status = 0
            stdout = '/run/podman/io.podman'
            stderr = ''
        mock_execute.return_value = FakeProcess()
        self.assertEqual(
            podman.discover_podman_socket(),
            '/run/podman/io.podman'
        )

    @mock.patch('tobiko.shell.sh.execute')
    def test_discover_podman_socket_none_result(self, mock_execute):
        class FakeProcess:
            exit_status = 1
            stdout = ''
            stderr = 'boom'
        mock_execute.return_value = FakeProcess()
        self.assertRaises(
            podman.PodmanSocketNotFoundError,
            podman.discover_podman_socket
        )

    @mock.patch('tobiko.shell.sh.execute')
    def test_discover_podman_socket_with_exit_code(self, mock_execute):
        class FakeProcess:
            exit_status = 0
            stdout = ''
            stderr = 'boom'
        mock_execute.return_value = FakeProcess()
        self.assertRaises(
            podman.PodmanSocketNotFoundError,
            podman.discover_podman_socket
        )

    @mock.patch('tobiko.shell.sh.execute')
    def test_is_podman_running(self, mock_execute):
        class FakeProcess:
            exit_status = 0
            stdout = '/run/podman/io.podman'
            stderr = ''
        mock_execute.return_value = FakeProcess()
        self.assertEqual(podman.is_podman_running(), True)

    @mock.patch('tobiko.shell.sh.execute')
    def test_is_podman_running_without_socket(self, mock_execute):
        class FakeProcess:
            exit_status = 1
            stdout = ''
            stderr = 'boom'
        mock_execute.return_value = FakeProcess()
        self.assertEqual(podman.is_podman_running(), False)
