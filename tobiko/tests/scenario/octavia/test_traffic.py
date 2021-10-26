# Copyright (c) 2019 Red Hat
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
from tobiko.openstack import keystone
from tobiko.openstack import octavia
from tobiko.openstack import stacks


@keystone.skip_if_missing_service(name='octavia')
class OctaviaBasicTrafficScenarioTest(testtools.TestCase):
    """Octavia traffic scenario test.

    Create a load balancer with 2 members that run a server application,
    Create a client that is connected to the load balancer VIP port,
    Generate network traffic from the client to the load balanacer.
    """
    loadbalancer_stack = tobiko.required_setup_fixture(
        stacks.OctaviaLoadbalancerStackFixture)

    listener_stack = tobiko.required_setup_fixture(
        stacks.OctaviaListenerStackFixture)

    pool_stack = tobiko.required_setup_fixture(
        stacks.OctaviaPoolStackFixture)

    member1_stack = tobiko.required_setup_fixture(
        stacks.OctaviaMemberServerStackFixture)

    member2_stack = tobiko.required_setup_fixture(
        stacks.OctaviaOtherMemberServerStackFixture)

    def setUp(self):
        # pylint: disable=no-member
        super(OctaviaBasicTrafficScenarioTest, self).setUp()

        # Wait for Octavia objects' provisioning status to be ACTIVE
        # and reachable
        octavia.wait_for_active_and_functional_members_and_lb(
            members=[self.member1_stack,
                     self.member2_stack],
            pool_id=self.pool_stack.pool_id,
            lb_protocol=self.listener_stack.lb_protocol,
            lb_port=self.listener_stack.lb_port,
            loadbalancer_id=self.loadbalancer_stack.loadbalancer_id)

        octavia.wait_for_octavia_service(
            loadbalancer_id=self.loadbalancer_stack.loadbalancer_id)

        octavia.wait_for_members_to_be_reachable(
            members=[self.member1_stack, self.member2_stack],
            lb_protocol=self.listener_stack.lb_protocol,
            lb_port=self.listener_stack.lb_port
        )

    @pytest.mark.flaky(reruns=3)
    def test_traffic(self):
        octavia.check_members_balanced(
            pool_id=self.pool_stack.pool_id,
            ip_address=self.loadbalancer_stack.floating_ip_address,
            lb_algorithm=self.pool_stack.lb_algorithm,
            protocol=self.listener_stack.lb_protocol,
            port=self.listener_stack.lb_port)
