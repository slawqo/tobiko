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


from tobiko.shell import sh
from tobiko.tests import unit


class ShellCommandTest(unit.TobikoUnitTest):

    def test_from_str(self):
        result = sh.shell_command('ls -lh *.py')
        self.assertIsInstance(result, sh.ShellCommand)
        self.assertEqual(('ls', '-lh', '*.py'), result)
        self.assertEqual("ls -lh *.py", str(result))

    def test_from_str_with_quotes(self):
        result = sh.shell_command('ls -lh "with quotes"')
        self.assertIsInstance(result, sh.ShellCommand)
        self.assertEqual(('ls', '-lh', "with quotes"), result)
        self.assertEqual("ls -lh 'with quotes'", str(result))

    def test_from_sequence(self):
        result = sh.shell_command(['ls', '-lh', '*.py'])
        self.assertIsInstance(result, sh.ShellCommand)
        self.assertEqual(('ls', '-lh', '*.py'), result)
        self.assertEqual("ls -lh *.py", str(result))

    def test_from_sequence_with_quotes(self):
        result = sh.shell_command(['ls', '-lh', "with quotes"])
        self.assertIsInstance(result, sh.ShellCommand)
        self.assertEqual(('ls', '-lh', "with quotes"), result)
        self.assertEqual("ls -lh 'with quotes'", str(result))

    def test_from_shell_command(self):
        other = sh.shell_command(['ls', '-lh', '*.py'])
        result = sh.shell_command(other)
        self.assertIs(other, result)

    def test_add_str(self):
        base = sh.shell_command('ssh pippo@clubhouse.mouse')
        result = base + 'ls -lh *.py'
        self.assertEqual(('ssh', 'pippo@clubhouse.mouse', 'ls', '-lh', '*.py'),
                         result)
        self.assertEqual("ssh pippo@clubhouse.mouse ls -lh *.py",
                         str(result))

    def test_add_str_with_quotes(self):
        base = sh.shell_command('sh -c')
        result = base + "'echo Hello!'"
        self.assertIsInstance(result, sh.ShellCommand)
        self.assertEqual(('sh', '-c', "echo Hello!"), result)
        self.assertEqual("sh -c 'echo Hello!'", str(result))

    def test_add_sequence(self):
        base = sh.shell_command('ssh pippo@clubhouse.mouse')
        result = base + ['ls', '-lh', '*.py']
        self.assertEqual(('ssh', 'pippo@clubhouse.mouse', 'ls', '-lh', '*.py'),
                         result)
        self.assertEqual("ssh pippo@clubhouse.mouse ls -lh *.py",
                         str(result))

    def test_add_sequence_with_quotes(self):
        base = sh.shell_command('sh -c')
        result = base + ['echo Hello!']
        self.assertIsInstance(result, sh.ShellCommand)
        self.assertEqual(('sh', '-c', "echo Hello!"), result)
        self.assertEqual("sh -c 'echo Hello!'", str(result))

    def test_add_shell_command(self):
        base = sh.shell_command('ssh pippo@clubhouse.mouse')
        result = base + sh.shell_command(['ls', '-lh', '*.py'])
        self.assertEqual(('ssh', 'pippo@clubhouse.mouse', 'ls', '-lh', '*.py'),
                         result)
        self.assertEqual("ssh pippo@clubhouse.mouse ls -lh *.py",
                         str(result))

    def test_add_shell_command_with_quotes(self):
        base = sh.shell_command('sh -c')
        result = base + sh.shell_command(['echo Hello!'])
        self.assertIsInstance(result, sh.ShellCommand)
        self.assertEqual(('sh', '-c', "echo Hello!"), result)
        self.assertEqual("sh -c 'echo Hello!'", str(result))
