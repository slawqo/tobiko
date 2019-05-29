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

import sys
import unittest

import testtools

from tobiko import config
from tobiko.shell import sh


CONF = config.CONF


class LocalExecuteTest(testtools.TestCase):

    ssh_client = None
    shell = '/bin/sh -c'

    def execute(self, command, **kwargs):
        kwargs.setdefault('shell', self.shell)
        kwargs.setdefault('ssh_client', self.ssh_client)
        return sh.execute(command, **kwargs)

    def test_execute_string(self):
        result = self.execute('true')
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'true'],
                timeout=None, exit_status=0, stdout='', stderr=''),
            result)

    def test_execute_list(self):
        result = self.execute(['echo', 'something'])
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'echo something'],
                timeout=None, exit_status=0, stdout='something\n', stderr=''),
            result)

    def test_execute_writing_to_stdout(self):
        result = self.execute('echo something')
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'echo something'],
                timeout=None, exit_status=0, stdout='something\n', stderr=''),
            result)

    def test_execute_writing_to_stderr(self):
        result = self.execute('echo something >&2')
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'echo something >&2'],
                timeout=None, exit_status=0, stdout='', stderr='something\n'),
            result)

    def test_execute_reading_from_stdin(self):
        result = self.execute('cat', stdin='some input\n')
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'cat'],
                timeout=None, exit_status=0, stdout='some input\n',
                stderr=''),
            result)

    def test_execute_failing_command(self):
        ex = self.assertRaises(sh.ShellCommandFailed, self.execute, 'exit 15')
        self.assertEqual('', ex.stdout)
        self.assertEqual('', ex.stderr)
        self.assertEqual(15, ex.exit_status)
        self.assertEqual(['/bin/sh', '-c', 'exit 15'], ex.command)

    def test_execute_failing_command_writing_to_stdout(self):
        ex = self.assertRaises(sh.ShellCommandFailed, self.execute,
                               'echo something; exit 8')
        self.assertEqual('something\n', ex.stdout)
        self.assertEqual('', ex.stderr)
        self.assertEqual(8, ex.exit_status)
        self.assertEqual(['/bin/sh', '-c', 'echo something; exit 8'],
                         ex.command)

    def test_execute_failing_command_writing_to_stderr(self):
        ex = self.assertRaises(sh.ShellCommandFailed, self.execute,
                               'echo something >&2; exit 7')
        self.assertEqual('', ex.stdout)
        self.assertEqual('something\n', ex.stderr)
        self.assertEqual(7, ex.exit_status)
        self.assertEqual(['/bin/sh', '-c', 'echo something >&2; exit 7'],
                         ex.command)

    @unittest.skipIf(sys.version_info < (3, 3),
                     'timeout not implemented for Python version < 3.3')
    def test_execute_with_timeout(self):
        result = self.execute('true', timeout=30.)
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'true'],
                timeout=30, exit_status=0, stdout='',
                stderr=''),
            result)

    @unittest.skipIf(sys.version_info < (3, 3),
                     'timeout not implemented for Python version < 3.3')
    def test_execute_with_timeout_expired(self):
        ex = self.assertRaises(sh.ShellTimeoutExpired, self.execute,
                               'echo out; echo err >&2; sleep 30',
                               timeout=.01)
        self.assertEqual(['/bin/sh', '-c',
                          'echo out; echo err >&2; sleep 30'],
                         ex.command)
