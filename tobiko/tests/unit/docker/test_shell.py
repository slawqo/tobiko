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

from tobiko import docker
from tobiko.tests import unit


# This class help us to emulate tobiko.shell.sh.execute
# to simulate errors or not and test the tobiko.docker._shell module
class FakeProcess:
    exit_status = 0
    stdout = ''
    stderr = ''


class TestShell(unit.TobikoUnitTest):

    def setUp(self):
        super(TestShell, self).setUp()
        self.fproc = FakeProcess()

    @mock.patch('tobiko.shell.sh.execute')
    def test_discover_docker_urls_single(self, mock_execute):
        self.fproc.exit_status = 0
        self.fproc.stdout = 'root      1999  0.0  0.2 1456736 85272 ?' \
                            'Ssl  15:16   0:01 /usr/bin/dockerd -H fd:// ' \
                            '--containerd=/run/containerd/containerd.sock'
        self.fproc.stderr = ''
        mock_execute.return_value = self.fproc
        self.assertEqual(docker.discover_docker_urls(), ['fd://'])

    @mock.patch('tobiko.shell.sh.execute')
    def test_discover_docker_urls_multiple(self, mock_execute):
        self.fproc.exit_status = 0
        self.fproc.stdout = 'root      1999  0.0  0.2 1456736 85272 ?' \
                            'Ssl  15:16   0:01 /usr/bin/dockerd -H fd:// ' \
                            '-H fd:// ' \
                            '--containerd=/run/containerd/containerd.sock'
        self.fproc.stderr = ''
        mock_execute.return_value = self.fproc
        self.assertEqual(docker.discover_docker_urls(), ['fd://', 'fd://'])

    @mock.patch('tobiko.shell.sh.execute')
    def test_discover_docker_urls_separated(self, mock_execute):
        self.fproc.exit_status = 0
        self.fproc.stdout = 'root      1999  0.0  0.2 1456736 85272 ?' \
                            'Ssl  15:16   0:01 /usr/bin/dockerd -H fd:// ' \
                            '--containerd=/run/containerd/containerd.sock ' \
                            '-H boom'
        self.fproc.stderr = ''
        mock_execute.return_value = self.fproc
        self.assertEqual(docker.discover_docker_urls(), ['fd://', 'boom'])

    @mock.patch('tobiko.shell.sh.execute')
    def test_discover_docker_urls_many_daemons(self, mock_execute):
        self.fproc.exit_status = 0
        self.fproc.stdout = 'root      1999  0.0  0.2 1456736 85272 ?' \
                            'Ssl  15:16   0:01 /usr/bin/dockerd ' \
                            '-H fd://  -H boom ' \
                            '--containerd=/run/containerd/containerd.sock\n' \
                            'root      1999  0.0  0.2 1456736 85272 ?' \
                            'Ssl  15:16   0:01 /usr/bin/dockerd -H foo ' \
                            '--containerd=/run/containerd/containerd.sock ' \
                            '-H bar'
        self.fproc.stderr = ''
        mock_execute.return_value = self.fproc
        self.assertEqual(docker.discover_docker_urls(),
                         ['fd://', 'boom', 'foo', 'bar'])

    @mock.patch('tobiko.shell.sh.execute')
    def test_discover_docker_urls_no_daemons(self, mock_execute):
        self.fproc.exit_status = 0
        self.fproc.stdout = ''
        self.fproc.stderr = ''
        mock_execute.return_value = self.fproc
        self.assertRaises(docker.DockerUrlNotFoundError,
                          docker.discover_docker_urls)

    @mock.patch('tobiko.shell.sh.execute')
    def test_is_docker_running(self, mock_execute):
        self.fproc.exit_status = 0
        self.fproc.stdout = 'root      1999  0.0  0.2 1456736 85272 ?' \
                            'Ssl  15:16   0:01 /usr/bin/dockerd ' \
                            '-H fd://  -H boom ' \
                            '--containerd=/run/containerd/containerd.sock\n' \
                            'root      1999  0.0  0.2 1456736 85272 ?' \
                            'Ssl  15:16   0:01 /usr/bin/dockerd -H foo ' \
                            '--containerd=/run/containerd/containerd.sock ' \
                            '-H bar'
        self.fproc.stderr = ''
        mock_execute.return_value = self.fproc
        self.assertEqual(docker.is_docker_running(), True)

    @mock.patch('tobiko.shell.sh.execute')
    def test_is_docker_running_without_results(self, mock_execute):
        self.fproc.exit_status = 0
        self.fproc.stdout = ''
        self.fproc.stderr = ''
        mock_execute.return_value = self.fproc
        self.assertEqual(docker.is_docker_running(), False)

    @mock.patch('tobiko.shell.sh.execute')
    def test_is_docker_running_exit_1(self, mock_execute):
        self.fproc.exit_status = 1
        self.fproc.stdout = 'root      1999  0.0  0.2 1456736 85272 ?' \
                            'Ssl  15:16   0:01 /usr/bin/dockerd ' \
                            '-H fd://  -H boom ' \
                            '--containerd=/run/containerd/containerd.sock\n' \
                            'root      1999  0.0  0.2 1456736 85272 ?' \
                            'Ssl  15:16   0:01 /usr/bin/dockerd -H foo ' \
                            '--containerd=/run/containerd/containerd.sock ' \
                            '-H bar'
        self.fproc.stderr = ''
        mock_execute.return_value = self.fproc
        self.assertEqual(docker.is_docker_running(), False)

    @mock.patch('tobiko.shell.sh.execute')
    def test_is_docker_running_error_exist_but_exit_0(self, mock_execute):
        self.fproc.exit_status = 0
        self.fproc.stdout = ''
        self.fproc.stderr = 'boom'
        mock_execute.return_value = self.fproc
        self.assertEqual(docker.is_docker_running(), False)
