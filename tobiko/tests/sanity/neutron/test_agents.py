# Copyright (c) 2020 Red Hat
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

import pytest
import testtools

from tobiko.openstack import tests


@pytest.mark.minimal
class NeutronAgentTest(testtools.TestCase):

    def test_agents_are_alive(self):
        tests.test_neutron_agents_are_alive()

    def test_alive_agents_are_consistent_along_time(self):
        tests.test_alive_agents_are_consistent_along_time()
