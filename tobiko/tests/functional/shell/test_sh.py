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


class ExecuteTest(testtools.TestCase):

    def test_execute_string(self):
        result = sh.execute('true', shell='/bin/sh -c')
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'true'],
                timeout=None, exit_status=0, stdout='', stderr=''),
            result)

    def test_execute_list(self):
        result = sh.execute(['echo', 'something'], shell='/bin/sh -c')
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'echo something'],
                timeout=None, exit_status=0, stdout='something\n', stderr=''),
            result)

    def test_execute_writing_to_stdout(self):
        result = sh.execute('echo something', shell='/bin/sh -c')
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'echo something'],
                timeout=None, exit_status=0, stdout='something\n', stderr=''),
            result)

    def test_execute_writing_to_stderr(self):
        result = sh.execute('echo something >&2', shell='/bin/sh -c')
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'echo something >&2'],
                timeout=None, exit_status=0, stdout='', stderr='something\n'),
            result)

    def test_execute_failing_command(self):
        ex = self.assertRaises(sh.ShellCommandFailed, sh.execute, 'exit 15',
                               shell='/bin/sh -c')
        self.assertEqual('', ex.stdout)
        self.assertEqual('', ex.stderr)
        self.assertEqual(15, ex.exit_status)
        self.assertEqual(['/bin/sh', '-c', 'exit 15'], ex.command)

    def test_execute_failing_command_writing_to_stdout(self):
        ex = self.assertRaises(sh.ShellCommandFailed, sh.execute,
                               'echo something; exit 8', shell='/bin/sh -c')
        self.assertEqual('something\n', ex.stdout)
        self.assertEqual('', ex.stderr)
        self.assertEqual(8, ex.exit_status)
        self.assertEqual(['/bin/sh', '-c', 'echo something; exit 8'],
                         ex.command)

    def test_execute_failing_command_writing_to_stderr(self):
        ex = self.assertRaises(sh.ShellCommandFailed, sh.execute,
                               'echo something >&2; exit 7',
                               shell='/bin/sh -c')
        self.assertEqual('', ex.stdout)
        self.assertEqual('something\n', ex.stderr)
        self.assertEqual(7, ex.exit_status)
        self.assertEqual(['/bin/sh', '-c', 'echo something >&2; exit 7'],
                         ex.command)

    def test_execute_with_timeout(self):
        result = sh.execute('true', timeout=30., shell='/bin/sh -c')
        expected_timeout = None if sys.version_info < (3, 3) else 30.
        self.assertEqual(
            sh.ShellExecuteResult(
                command=['/bin/sh', '-c', 'true'],
                timeout=expected_timeout, exit_status=0, stdout='',
                stderr=''),
            result)

    @unittest.skipIf(sys.version_info < (3, 3),
                     'not implemented for Python version < 3.3')
    def test_execute_with_timeout_expired(self):
        ex = self.assertRaises(sh.ShellTimeoutExpired, sh.execute,
                               'echo out; echo err >&2; sleep 30',
                               timeout=.01, shell='/bin/sh -c')
        self.assertEqual(['/bin/sh', '-c',
                          'echo out; echo err >&2; sleep 30'],
                         ex.command)
