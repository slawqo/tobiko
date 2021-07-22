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

    client_stack = tobiko.required_setup_fixture(
        stacks.OctaviaClientServerStackFixture)

    members_count = 2

    def setUp(self):
        # pylint: disable=no-member
        super(OctaviaBasicTrafficScenarioTest, self).setUp()

        self.loadbalancer_vip = self.loadbalancer_stack.loadbalancer_vip
        self.loadbalancer_port = self.listener_stack.lb_port
        self.loadbalancer_protocol = self.listener_stack.lb_protocol

        octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                                status=octavia.ACTIVE,
                                get_client=octavia.get_member,
                                object_id=self.pool_stack.pool_id,
                                member_id=self.member1_stack.member_id)

        octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                                status=octavia.ACTIVE,
                                get_client=octavia.get_member,
                                object_id=self.pool_stack.pool_id,
                                member_id=self.member2_stack.member_id)

        # Wait for LB is provisioned and ACTIVE
        octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                                status=octavia.ACTIVE,
                                get_client=octavia.get_loadbalancer,
                                object_id=(
                                    self.loadbalancer_stack.loadbalancer_id))

    @property
    def loadbalancer(self):
        return self.loadbalancer_stack

    def test_traffic(self):
        octavia.check_members_balanced(self.pool_stack,
                                       self.client_stack,
                                       self.members_count,
                                       self.loadbalancer_vip,
                                       self.loadbalancer_protocol,
                                       self.loadbalancer_port)
