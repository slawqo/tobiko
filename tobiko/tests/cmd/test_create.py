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

from tobiko.cmd import create
from tobiko.common import constants
from tobiko.tests.base import TobikoTest


class CreateUtilTest(TobikoTest):

    @mock.patch('sys.argv', ['tobiko-create'])
    def test_init(self):
        cmd = create.CreateUtil()
        self.assertIsNotNone(cmd.clientManager)
        self.assertTrue(os.path.isdir(cmd.templates_dir))
        self.assertIsNotNone(cmd.stackManager)
        self.assertIsNotNone(cmd.parser)
        self.assertFalse(cmd.args.all)
        self.assertIsNone(cmd.args.stack)

    @mock.patch('sys.argv', ['tobiko-create', '--all'])
    def test_init_with_all(self):
        cmd = create.CreateUtil()
        self.assertIsNotNone(cmd.clientManager)
        self.assertTrue(os.path.isdir(cmd.templates_dir))
        self.assertIsNotNone(cmd.stackManager)
        self.assertIsNotNone(cmd.parser)
        self.assertTrue(cmd.args.all)
        self.assertIsNone(cmd.args.stack)

    @mock.patch('sys.argv', ['tobiko-create', '--stack', 'my-stack'])
    def test_init_with_stack(self):
        cmd = create.CreateUtil()
        self.assertIsNotNone(cmd.clientManager)
        self.assertTrue(os.path.isdir(cmd.templates_dir))
        self.assertIsNotNone(cmd.stackManager)
        self.assertIsNotNone(cmd.parser)
        self.assertFalse(cmd.args.all)
        self.assertEqual('my-stack', cmd.args.stack)


class TestMain(TobikoTest):

    @mock.patch('sys.argv', ['tobiko-create', '--stack', 'test_floatingip'])
    def test_main_with_stack(self):
        # pylint: disable=no-value-for-parameter
        self._test_main(stack_names=['test_floatingip'],
                        walk_dir=False)

    @mock.patch('sys.argv', ['tobiko-create'])
    def test_main(self):
        # pylint: disable=no-value-for-parameter
        self._test_main(stack_names=['test_floatingip', 'test_mtu'],
                        walk_dir=True)

    @mock.patch('sys.argv', ['tobiko-create', '--all'])
    def test_main_with_all(self):
        # pylint: disable=no-value-for-parameter
        self._test_main(stack_names=['test_mtu', 'test_security_groups'],
                        walk_dir=True)

    @mock.patch('heatclient.client.Client')
    @mock.patch('os.walk')
    def _test_main(self, mock_walk, MockClient, stack_names, walk_dir):
        # Break wait for stack status loop
        MockClient().stacks.get().stack_status = constants.COMPLETE_STATUS
        mock_walk.return_value = [(None, None, [(name + '.yaml')
                                                for name in stack_names])]

        create.main()

        # Check stack is created
        MockClient().stacks.create.assert_has_calls(
            [mock.call(parameters=constants.DEFAULT_PARAMS,
                       stack_name=stack_name,
                       template=mock.ANY)
             for stack_name in stack_names])

        if walk_dir:
            mock_walk.assert_called_once_with(mock.ANY)
        else:
            mock_walk.assert_not_called()
