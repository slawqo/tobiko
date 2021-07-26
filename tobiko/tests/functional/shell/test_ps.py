# Copyright (c) 2020 Red Hat, Inc.
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

from oslo_log import log
import testtools

import tobiko
from tobiko.openstack import stacks
from tobiko.openstack import topology
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


class LocalPsTest(testtools.TestCase):

    @property
    def ssh_client(self) -> ssh.SSHClientType:
        return False

    def test_list_processes(self):
        processes = sh.list_processes(ssh_client=self.ssh_client)
        self._check_processes(processes,
                              is_kernel=False)

    def test_list_kernel_processes(self):
        processes = sh.list_kernel_processes(ssh_client=self.ssh_client)
        self._check_processes(processes=processes, is_kernel=True)

    def test_list_all_processes(self):
        processes = sh.list_all_processes(ssh_client=self.ssh_client)
        self._check_processes(processes=processes, is_kernel=None)

    def test_list_processes_with_pid(self):
        processes = sh.list_processes(ssh_client=self.ssh_client)
        processes_with_pid = sh.list_processes(pid=processes[0].pid,
                                               ssh_client=self.ssh_client)
        self.assertEqual(processes[:1], processes_with_pid)

    def test_list_processes_with_command(self):
        processes = sh.list_processes(command='systemd',
                                      ssh_client=self.ssh_client)
        for process in processes:
            self.assertTrue(process.command.startswith('systemd'), process)

    def test_list_processes_with_command_line(self):
        cat_process = sh.process('cat -',
                                 ssh_client=self.ssh_client).execute()
        self.addCleanup(cat_process.kill)
        processes = sh.list_processes(command_line='cat -',
                                      ssh_client=self.ssh_client)
        for process in processes:
            self.assertEqual('cat', process.command)
            self.assertEqual(('cat', '-'), process.command_line)
        cat_process.kill()
        sh.wait_for_processes(command_line='cat -',
                              timeout=30.,
                              ssh_client=self.ssh_client)

    def test_list_processes_with_exact_command(self):
        processes = sh.list_processes(command='^systemd$',
                                      ssh_client=self.ssh_client)
        self.assertEqual(processes.with_attributes(command='systemd'),
                         processes)

    def _check_processes(self, processes, is_kernel):
        self.assertIsInstance(processes, tobiko.Selection)
        for process in processes:
            self.assertGreater(process.pid, 0)
            self.assertIs(
                (process.command.startswith('[') and
                 process.command.endswith(']')),
                process.is_kernel)
            if is_kernel is not None:
                self.assertIs(bool(is_kernel), process.is_kernel)

    def test_wait_for_processes(self):
        # assume the PID of the first execution of PS process is not more there
        # at the second execution
        process = sh.list_processes(command='ps',
                                    ssh_client=self.ssh_client)[-1]
        sh.wait_for_processes(pid=process.pid,
                              command='ps',
                              timeout=30.,
                              ssh_client=self.ssh_client)

    def test_wait_for_processes_timeout(self):
        # assume there are always to be running processes on host
        ex = self.assertRaises(sh.PsWaitTimeout, sh.wait_for_processes,
                               timeout=3.,
                               ssh_client=self.ssh_client)
        self.assertEqual(3., ex.timeout)
        self.assertEqual(sh.get_hostname(ssh_client=self.ssh_client),
                         ex.hostname)


class CirrosPsTest(LocalPsTest):

    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    @property
    def ssh_client(self) -> ssh.SSHClientType:
        return self.stack.ssh_client


class SSHPsTest(LocalPsTest):

    @property
    def ssh_client(self) -> ssh.SSHClientType:
        ssh_client = ssh.ssh_proxy_client()
        if isinstance(ssh_client, ssh.SSHClientFixture):
            return ssh_client

        nodes = topology.list_openstack_nodes()
        for node in nodes:
            if isinstance(node.ssh_client, ssh.SSHClientFixture):
                return ssh_client
        tobiko.skip_test('No such SSH server host to connect to')
