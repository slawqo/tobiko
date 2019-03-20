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

from tobiko.cmd import delete
from tobiko.common.managers import stack as stack_manager
from tobiko.tests.cmd import test_base


class DeleteTest(test_base.TobikoCMDTest):

    command_name = 'tobiko-delete'
    command_class = delete.DeleteUtil

    def test_init(self, argv=None, all_stacks=False, stack=None, wait=False):
        # pylint: disable=arguments-differ,no-member
        cmd = super(DeleteTest, self).test_init(argv=argv)
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

        client = self.patch_get_heat_client().return_value
        client.stacks.list.return_value = [mock.Mock(stack_name=stack_name)
                                           for stack_name in stack_names[::2]]

        def client_get():

            for i, name in enumerate(stack_names):
                if wait:
                    # This would cause to wait for DELETE_COMPLETE status
                    yield mock.Mock(
                        stack_status=stack_manager.DELETE_IN_PROGRESS,
                        name=name)
                    if i % 2:
                        # Break wait for stack status loop with DELETE_COMPLETE
                        yield mock.Mock(
                            stack_status=stack_manager.DELETE_COMPLETE,
                            name=name)
                    else:
                        # Break wait for stack status loop with HTTPNotFound
                        yield exc.HTTPNotFound

        client.stacks.get.side_effect = client_get()

        delete.main()

        # Check stack is deleted
        client.stacks.delete.assert_has_calls(
            [mock.call(stack_name)
             for stack_name in stack_names[::2]])

        if walk_dir:
            mock_walk.assert_called()
            client.stacks.list.assert_called_once_with()
        else:
            client.stacks.list.assert_not_called()

        if wait:
            mock_sleep.assert_called()

    def test_main_with_stack(self):
        self.test_main(argv=['--stack', 'test_floatingip'],
                       stack_names=['test_floatingip'],
                       walk_dir=False)

    def test_main_with_all(self):
        self.test_main(argv=['--all'],
                       stack_names=['test_mtu', 'test_security_groups',
                                    'test_floatingip'])

    def test_main_with_wait(self):
        self.test_main(argv=['--wait'],
                       stack_names=['test_mtu', 'test_security_groups',
                                    'test_floatingip'],
                       wait=True)

    def test_main_with_w(self):
        self.test_main(argv=['-w'],
                       stack_names=['test_mtu', 'test_security_groups',
                                    'test_floatingip'],
                       wait=True)
