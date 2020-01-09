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

import testtools

import tobiko
from tobiko.openstack import stacks


class ServerGroupTestCase(testtools.TestCase):

    affinity_stack = tobiko.required_setup_fixture(
        stacks.AffinityServerGroupStackFixture)

    def test_affinity_server_group(self):
        group_id = self.affinity_stack.scheduler_group
        self.assertIsNotNone(group_id)

    anti_affinity_stack = tobiko.required_setup_fixture(
        stacks.AntiAffinityServerGroupStackFixture)

    def test_anti_affinity_server_group(self):
        group_id = self.anti_affinity_stack.scheduler_group
        self.assertIsNotNone(group_id)
