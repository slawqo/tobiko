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
import typing

import testtools

import tobiko
from tobiko.openstack import heat
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks


TEMPLATE_DIRS = [os.path.dirname(__file__)]


def random_string(length, letters=string.ascii_lowercase):
    return ''.join(random.choice(letters) for _ in range(length))


class MyStack(heat.HeatStackFixture):

    template = heat.heat_template_file(template_file='hot/my_stack.yaml',
                                       template_dirs=TEMPLATE_DIRS)

    input_text = random_string(8)


class HeatStackFixtureTest(testtools.TestCase):

    stack = tobiko.required_fixture(MyStack)

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


class EnsureNeutronQuotaLimitsFixture(MyStack):

    requirements = {'network': 100, 'subnet': 100, 'router': 10}

    @property
    def neutron_required_quota_set(self) -> typing.Dict[str, int]:
        return self.requirements


class EnsureNovaQuotaLimitsFixture(MyStack):

    requirements = {'cores': 20, 'instances': 10}

    @property
    def nova_required_quota_set(self) -> typing.Dict[str, int]:
        return self.requirements


class EnsureQuotaLimitsTest(testtools.TestCase):

    def test_ensure_neutron_quota_limits(self):
        stack = EnsureNeutronQuotaLimitsFixture(stack_name=self.id())
        self.useFixture(stack)
        quota_set = neutron.get_neutron_quota_set(detail=True)
        for name, requirement in stack.requirements.items():
            quota = quota_set[name]
            self.assertGreaterEqual(int(quota['limit']),
                                    requirement +
                                    max(0, int(quota['used'])) -
                                    max(0, int(quota['reserved'])))

    def test_ensure_nova_quota_limits(self):
        stack = EnsureNovaQuotaLimitsFixture(stack_name=self.id())
        self.useFixture(stack)
        quota_set = nova.get_nova_quota_set(detail=True)
        for name, requirement in stack.requirements.items():
            quota = getattr(quota_set, name)
            if int(quota['limit']) > 0:
                self.assertGreaterEqual(int(quota['limit']),
                                        int(requirement) +
                                        max(0, int(quota['in_use'])) -
                                        max(0, int(quota['reserved'])))
            else:
                self.assertEqual(int(quota['limit']), -1)


@keystone.skip_unless_has_keystone_credentials()
class StackTest(testtools.TestCase):

    router_stack = tobiko.required_fixture(stacks.RouterStackFixture)

    def test_find_stack(self):
        stack = self.router_stack.stack
        self.assertIsInstance(stack, heat.STACK_CLASSES)
        result = heat.find_stack(name=stack.stack_name)
        self.assertEqual(stack.stack_name, result.stack_name)

    def test_list_stacks(self):
        stack = self.router_stack.stack
        result = heat.list_stacks()
        self.assertIsInstance(result, tobiko.Selection)
        self.assertEqual(stack.id,
                         result.with_attributes(id=stack.id).unique.id)


@keystone.skip_unless_has_keystone_credentials()
class ResourceTest(testtools.TestCase):

    router_stack = tobiko.required_fixture(stacks.RouterStackFixture)

    def test_find_resource(self):
        self.router_stack.wait_for_create_complete()
        resource = heat.list_resources(stack=self.router_stack).first
        result = heat.find_resource(
            stack=self.router_stack,
            physical_resource_id=resource.physical_resource_id)
        self.assertIsInstance(resource, heat.RESOURCE_CLASSES)
        self.assertEqual(resource.physical_resource_id,
                         result.physical_resource_id)

    def test_list_resource(self):
        self.router_stack.wait_for_create_complete()
        resources = heat.list_resources(stack=self.router_stack)
        self.assertIsInstance(resources, tobiko.Selection)
        self.assertNotEqual([], resources)
        self.assertEqual(resources,
                         resources.with_attributes(
                             stack_name=self.router_stack.stack_name))
