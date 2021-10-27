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

import os

import testtools

from tobiko.shell import sh


class WcTest(testtools.TestCase):

    def test_get_file_size(self):
        file_name = os.path.join(sh.make_temp_dir(),
                                 self.id())
        sh.execute(f'echo "{self.id()}" > "{file_name}"')
        file_size = sh.get_file_size(file_name)
        self.assertEqual(len(self.id()) + 1, file_size)

    def test_get_file_size_when_empty(self):
        file_name = os.path.join(sh.make_temp_dir(),
                                 self.id())
        sh.execute(f'touch "{file_name}"')
        file_size = sh.get_file_size(file_name)
        self.assertEqual(0, file_size)

    def test_get_file_size_when_not_found(self):
        file_name = os.path.join(sh.make_temp_dir(),
                                 self.id())
        ex = self.assertRaises(sh.ShellCommandFailed,
                               sh.get_file_size,
                               file_name)
        self.assertEqual(1, ex.exit_status)
        self.assertIn(
            ex.stderr.strip(),
            [f"wc: {file_name}: No such file or directory",
             f"wc: {file_name}: open: No such file or directory"])

    def test_assert_file_size(self):
        file_name = os.path.join(sh.make_temp_dir(),
                                 self.id())
        sh.execute(f'echo "{self.id()}" > "{file_name}"')
        sh.assert_file_size(len(self.id()) + 1, file_name)

    def test_assert_file_size_when_empty(self):
        file_name = os.path.join(sh.make_temp_dir(),
                                 self.id())
        sh.execute(f'touch "{file_name}"')
        sh.assert_file_size(0, file_name)

    def test_assert_file_size_when_not_found(self):
        file_name = os.path.join(sh.make_temp_dir(),
                                 self.id())
        ex = self.assertRaises(sh.ShellCommandFailed,
                               sh.assert_file_size,
                               1, file_name)
        self.assertEqual(1, ex.exit_status)
        self.assertIn(
            ex.stderr.strip(),
            [f"wc: {file_name}: No such file or directory",
             f"wc: {file_name}: open: No such file or directory"])

    def test_assert_file_size_when_mismatch(self):
        file_name = os.path.join(sh.make_temp_dir(),
                                 self.id())
        sh.execute(f'echo "{self.id()}" > "{file_name}"')
        ex = self.assertRaises(testtools.matchers.MismatchError,
                               sh.assert_file_size,
                               1, file_name)
        self.assertEqual(f'1 != {len(self.id()) + 1}', str(ex))
