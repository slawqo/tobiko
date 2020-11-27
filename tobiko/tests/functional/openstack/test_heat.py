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

import os
import random
import string

import testtools

import tobiko
from tobiko.openstack import heat


TEMPLATE_DIRS = [os.path.dirname(__file__)]


def random_string(length, letters=string.ascii_lowercase):
    return ''.join(random.choice(letters) for _ in range(length))


class MyStack(heat.HeatStackFixture):

    template = heat.heat_template_file(template_file='hot/my_stack.yaml',
                                       template_dirs=TEMPLATE_DIRS)

    input_text = random_string(8)


class HeatStackFixtureTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(MyStack)

    def test_get_stack(self):
        self.stack.wait_for_create_complete()
        stack = self.stack.get_stack()
        self.assertIsNotNone(stack)
        self.assertEqual(tobiko.get_fixture_name(MyStack), stack.stack_name)
        self.assertIsInstance(stack.id, str)
        self.assertIsInstance(stack.stack_status, str)

    def test_get_fixture_with_fixture_id_0(self):
        fixture_0 = tobiko.get_fixture(MyStack, fixture_id=0)
        self.assertIs(fixture_0, self.stack)

    def test_get_fixture_with_fixture_id_1(self):
        fixture_0 = tobiko.get_fixture(MyStack)
        fixture_1 = tobiko.get_fixture(MyStack, fixture_id=1)
        self.assertIsNot(fixture_0, fixture_1)
        stack_0 = tobiko.setup_fixture(fixture_0).get_stack()
        stack_1 = tobiko.setup_fixture(fixture_1).get_stack()
        self.assertNotEqual(stack_0.id, stack_1.id)
        self.assertEqual(tobiko.get_fixture_name(MyStack), stack_0.stack_name)
        self.assertEqual(tobiko.get_fixture_name(MyStack) + '-1',
                         stack_1.stack_name)
