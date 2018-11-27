# Copyright (c) 2018 Red Hat
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

import os.path

import mock

from tobiko.cmd import list
from tobiko.common import constants
from tobiko.tests.base import TobikoTest


class ListUtilTest(TobikoTest):

    @mock.patch('sys.argv', ['tobiko-list'])
    def test_init(self):
        cmd = list.ListUtil()
        self.assertIsNotNone(cmd.clientManager)
        self.assertTrue(os.path.isdir(cmd.templates_dir))
        self.assertIsNotNone(cmd.stackManager)
        self.assertIsNotNone(cmd.parser)
        self.assertIsNone(cmd.args.action)

    @mock.patch('sys.argv', ['tobiko-list', '--stacks'])
    def test_init_with_stacks(self):
        self._test_init_with_stacks()

    @mock.patch('sys.argv', ['tobiko-list', '-s'])
    def test_init_with_s(self):
        self._test_init_with_stacks()

    def _test_init_with_stacks(self):
        cmd = list.ListUtil()
        self.assertIsNotNone(cmd.clientManager)
        self.assertTrue(os.path.isdir(cmd.templates_dir))
        self.assertIsNotNone(cmd.stackManager)
        self.assertIsNotNone(cmd.parser)
        self.assertEqual('list_stacks', cmd.args.action)

    @mock.patch('sys.argv', ['tobiko-list', '--templates'])
    def test_init_with_templates(self):
        self._test_init_with_templates()

    @mock.patch('sys.argv', ['tobiko-list', '-t'])
    def test_init_with_t(self):
        self._test_init_with_templates()

    def _test_init_with_templates(self):
        cmd = list.ListUtil()
        self.assertIsNotNone(cmd.clientManager)
        self.assertTrue(os.path.isdir(cmd.templates_dir))
        self.assertIsNotNone(cmd.stackManager)
        self.assertIsNotNone(cmd.parser)
        self.assertEqual('list_templates', cmd.args.action)


class TestMain(TobikoTest):

    @mock.patch('sys.argv', ['tobiko-list'])
    def test_main(self):
        self._test_main(stack_names=['test_floatingip', 'test_mtu'],
                        show_templates=True)

    @mock.patch('sys.argv', ['tobiko-list', '--stack'])
    def test_main_with_stacks(self):
        self._test_main(stack_names=['test_floatingip', 'test_mtu'],
                        show_templates=False)

    @mock.patch('sys.argv', ['tobiko-list', '-s'])
    def test_main_with_s(self):
        self._test_main(stack_names=['test_floatingip', 'test_mtu'],
                        show_templates=False)

    @mock.patch('sys.argv', ['tobiko-list', '--templates'])
    def test_main_with_templates(self):
        self._test_main(stack_names=['test_floatingip', 'test_mtu'],
                        show_templates=True)

    @mock.patch('sys.argv', ['tobiko-list', '-t'])
    def test_main_with_all(self):
        self._test_main(stack_names=['test_floatingip', 'test_mtu'],
                        show_templates=True)

    @mock.patch('heatclient.client.Client')
    @mock.patch('os.walk')
    @mock.patch('sys.stdout.write')
    def _test_main(self, mock_write, mock_walk, MockClient, stack_names,
                   show_templates):
        # Break wait for stack status loop
        MockClient().stacks.get().stack_status = constants.COMPLETE_STATUS
        mock_walk.return_value = [(None, None, [(name + '.yaml')
                                                for name in stack_names])]
        MockClient().stacks.list.return_value = [
            mock.Mock(stack_name=stack_name)
            for stack_name in stack_names[::2]]

        list.main()

        if show_templates:
            mock_write.assert_has_calls([mock.call(stack_name + '.yaml\n')
                                         for stack_name in stack_names])
        else:
            mock_write.assert_has_calls([mock.call(stack_name + '\n')
                                         for stack_name in stack_names[::2]])

        mock_walk.assert_called_once_with(mock.ANY)
