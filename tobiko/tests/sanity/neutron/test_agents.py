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

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import tests


@pytest.mark.minimal
class NeutronAgentTest(testtools.TestCase):

    def test_agents_are_alive(self):
        tests.test_neutron_agents_are_alive()

    def test_alive_agents_are_consistent_along_time(self):
        alive_agents = {agent['id']: agent
                        for agent in tests.test_neutron_agents_are_alive()}
        for attempt in tobiko.retry(sleep_time=5., count=5):
            agents = neutron.list_agents()
            actual = {agent['id']: agent
                      for agent in agents}
            self.assertEqual(set(alive_agents), set(actual),
                             'Agents appeared or disappeared')
            dead_agents = agents.with_items(alive=False)
            self.assertEqual([], dead_agents,
                             "Neutron agent(s) no more alive")
            if attempt.is_last:
                break
