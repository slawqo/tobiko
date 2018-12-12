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

import mock

from tobiko.cmd import list as list_cmd
from tobiko.common.managers import stack
from tobiko.tests.cmd import test_base


class ListTest(test_base.TobikoCMDTest):

    command_name = 'tobiko-list'
    command_class = list_cmd.ListUtil

    def test_init(self, argv=None, action=None):
        # pylint: disable=arguments-differ,no-member
        cmd = super(ListTest, self).test_init(argv=argv)
        self.assertIsNotNone(cmd.parser)
        self.assertEqual(action, cmd.args.action)

    def test_init_with_stacks(self):
        self.test_init(argv=['--stacks'],
                       action='list_stacks')

    def test_init_with_s(self):
        self.test_init(argv=['--stacks'],
                       action='list_stacks')

    def test_init_with_templates(self):
        self.test_init(argv=['--templates'],
                       action='list_templates')

    def test_init_with_t(self):
        self.test_init(argv=['-t'],
                       action='list_templates')

    def test_main(self, argv=None, stack_names=None, show_stacks=None):

        if stack_names is None:
            stack_names = ['test_mtu', 'test_floatingip']

        self.patch_argv(argv=argv)

        MockClient = self.patch('heatclient.client.Client')
        # Break wait for stack status loop
        MockClient().stacks.get().stack_status = stack.CREATE_COMPLETE
        MockClient().stacks.list.return_value = [
            mock.Mock(stack_name=stack_name)
            for stack_name in stack_names[::2]]

        mock_walk = self.patch('os.walk',
                               return_value=[(None, None, [(name + '.yaml')
                                             for name in stack_names])])

        mock_stdout_write = self.patch('sys.stdout.write')

        list_cmd.main()

        if show_stacks:
            mock_stdout_write.assert_has_calls(
                [mock.call(stack_name + '\n')
                 for stack_name in stack_names[::2]])
        else:
            mock_stdout_write.assert_has_calls(
                [mock.call(stack_name + '.yaml\n')
                 for stack_name in stack_names])

        mock_walk.assert_called()

    def test_main_with_stacks(self):
        self.test_main(argv=['--stack'],
                       stack_names=['test_floatingip', 'test_mtu'],
                       show_stacks=True)

    def test_main_with_s(self):
        self.test_main(argv=['-s'],
                       stack_names=['test_floatingip', 'test_security_groups'],
                       show_stacks=True)

    def test_main_with_templates(self):
        self.test_main(argv=['--templates'],
                       stack_names=['test_floatingip', 'test_mtu'],
                       show_stacks=False)

    def test_main_with_t(self):
        self.test_main(argv=['-t'],
                       stack_names=['test_floatingip', 'test_security_groups'],
                       show_stacks=False)
