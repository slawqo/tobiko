# Copyright 2019 Red Hat
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

import tobiko
from tobiko.openstack import glance
from tobiko.openstack import keystone
from tobiko.openstack import nova
from tobiko.openstack import tests


class MyServerStack(tests.TestServerCreationStack):
    pass


@keystone.skip_unless_has_keystone_credentials()
class ServerCreationTest(testtools.TestCase):

    def test_server_creation(self):
        all_servers_ids = {server.id for server in nova.list_servers()}

        stack = tests.test_server_creation()

        self.assertIsInstance(stack, tests.TestServerCreationStack)
        class_name = tobiko.get_fixture_name(tests.TestServerCreationStack)
        pid = os.getpid()
        self.assertEqual(f"{class_name}-{pid}-0", stack.stack_name)
        self.assertNotIn(stack.server_id, all_servers_ids)
        self.assertEqual('ACTIVE', nova.get_server(stack.server_id).status)

    def test_server_creation_with_stack(self):
        stack = tests.test_server_creation(stack=MyServerStack)
        self.assertIsInstance(stack, tests.TestServerCreationStack)

    def test_evacuable_server_creation(self):
        stack = tests.test_evacuable_server_creation()
        self.assertIsInstance(stack, tests.TestEvacuableServerCreationStack)
        self.assertIn('evacuable', glance.get_image(stack.image).tags)

    def test_server_creation_and_shutoff(self):
        stack = tests.test_server_creation_and_shutoff()
        self.assertIsInstance(stack, tests.TestServerCreationStack)
        self.assertEqual('SHUTOFF', nova.get_server(stack.server_id).status)

    def test_servers_creation(self):
        all_servers_ids = {server.id for server in nova.list_servers()}
        stacks = tests.test_servers_creation()
        self.assertEqual(2, len(stacks))
        pid = os.getpid()
        for i, stack in enumerate(stacks):
            self.assertIsInstance(stack, tests.TestServerCreationStack)
            class_name = tobiko.get_fixture_name(tests.TestServerCreationStack)
            self.assertEqual(f"{class_name}-{pid}-{i}", stack.stack_name)
            self.assertNotIn(stack.server_id, all_servers_ids)
            self.assertEqual('ACTIVE', nova.get_server(stack.server_id).status)
