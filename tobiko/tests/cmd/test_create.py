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

from heatclient import exc
import mock

from tobiko.cmd import create
from tobiko.common.managers import stack as stack_manager
from tobiko.common import constants
from tobiko.tests.cmd import test_base


class CreateTest(test_base.TobikoCMDTest):

    command_name = 'tobiko-create'
    command_class = create.CreateUtil

    def test_init(self, argv=None, all_stacks=False, stack=None, wait=False):
        # pylint: disable=arguments-differ,no-member
        cmd = super(CreateTest, self).test_init(argv=argv)
        self.assertIsNotNone(cmd.parser)
        self.assertIs(all_stacks, cmd.args.all)
        self.assertEqual(stack, cmd.args.stack)
        self.assertIs(wait, cmd.args.wait)
        return cmd

    def test_init_with_all(self):
        self.test_init(argv=['--all'], all_stacks=True)

    def test_init_with_stack(self):
        self.test_init(argv=['--stack', 'my-stack'], stack='my-stack')

    def test_init_with_wait(self):
        self.test_init(argv=['--wait'], wait=True)

    def test_init_with_w(self):
        self.test_init(argv=['-w'], wait=True)

    def test_main(self, argv=None, stack_names=None, walk_dir=True,
                  wait=False):

        if stack_names is None:
            stack_names = ['test_mtu', 'test_floatingip']

        self.patch_argv(argv=argv)

        mock_sleep = self.patch('time.sleep')

        mock_walk = self.patch('os.walk', return_value=[
            (None, None, [(name + '.yaml') for name in stack_names])])

        def mock_client_get():
            for name in stack_names:
                # This would cause to create stack
                yield exc.HTTPNotFound
                # This would cause to wait for CREATE_COMPLETE status
                yield mock.Mock(stack_status=stack_manager.CREATE_IN_PROGRESS,
                                name=name)
                if wait:
                    # Break wait for stack status loop
                    yield mock.Mock(stack_status=stack_manager.CREATE_COMPLETE,
                                    name=name)

        MockClient = self.patch('heatclient.client.Client')
        MockClient().stacks.get.side_effect = mock_client_get()

        create.main()

        # Check stack is created
        MockClient().stacks.create.assert_has_calls(
            [mock.call(parameters=constants.DEFAULT_PARAMS,
                       stack_name=stack_name,
                       template=mock.ANY)
             for stack_name in stack_names])

        if walk_dir:
            mock_walk.assert_called()

        if wait:
            mock_sleep.assert_called()

    def test_main_with_stack(self):
        self.test_main(argv=['--stack', 'test_floatingip'],
                       stack_names=['test_floatingip'], walk_dir=False)

    def test_main_with_all(self):
        self.test_main(argv=['--all'],
                       stack_names=['test_mtu', 'test_security_groups'])

    def test_main_with_wait(self):
        self.test_main(argv=['--wait'], wait=True)

    def test_main_with_w(self):
        self.test_main(argv=['-w'], wait=True)
