# Copyright (c) 2021 Red Hat
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
from oslo_log import log

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import octavia
from tobiko.openstack import stacks
from tobiko import tripleo


LOG = log.getLogger(__name__)


@keystone.skip_if_missing_service(name='octavia')
@tripleo.skip_if_missing_overcloud
class OctaviaBasicFaultTest(testtools.TestCase):
    """Octavia fault scenario test.

    Create a load balancer with 2 members that run a server application,
    Create a client that is connected to the load balancer VIP port,
    Generate network traffic from the client to the load balanacer VIP.
    Restart the amphora's compute node to create a failover.
    Reach the members to make sure they are ready to be checked.
    Generate network traffic again to verify Octavia functionality.
    """
    loadbalancer_stack = tobiko.required_setup_fixture(
        stacks.AmphoraIPv4LoadBalancerStack)

    listener_stack = tobiko.required_setup_fixture(
        stacks.HttpRoundRobinAmphoraIpv4Listener)

    def setUp(self):
        # pylint: disable=no-member
        super(OctaviaBasicFaultTest, self).setUp()

        # Wait for Octavia objects to be active
        LOG.info('Waiting for member '
                 f'{self.listener_stack.server_stack.stack_name} and '
                 f'for member '
                 f'{self.listener_stack.other_server_stack.stack_name} '
                 f'to be created...')
        self.listener_stack.wait_for_active_members()

        self.loadbalancer_stack.wait_for_octavia_service()

        self.listener_stack.wait_for_members_to_be_reachable()

        # Send traffic
        octavia.check_members_balanced(
            pool_id=self.listener_stack.pool_id,
            ip_address=self.loadbalancer_stack.floating_ip_address,
            lb_algorithm=self.listener_stack.lb_algorithm,
            protocol=self.listener_stack.lb_protocol,
            port=self.listener_stack.lb_port)

    def test_reboot_amphora_compute_node(self):
        amphora_compute_host = octavia.get_amphora_compute_node(
            loadbalancer_id=self.loadbalancer_stack.loadbalancer_id,
            lb_port=self.listener_stack.lb_port,
            lb_protocol=self.listener_stack.lb_protocol,
            ip_address=self.loadbalancer_stack.floating_ip_address)

        LOG.debug('Rebooting compute node...')

        # Reboot Amphora's compute node will initiate a failover
        amphora_compute_host.reboot_overcloud_node()

        LOG.debug('Compute node has been rebooted')

        # Wait for the LB to be updated
        try:
            self.loadbalancer_stack.wait_for_update_loadbalancer(timeout=30)

        except tobiko.RetryTimeLimitError:
            LOG.info('The restarted servers reached ACTIVE status after the'
                     ' LB finished its update process, hence no exception is'
                     ' being raised even though the update timeout was'
                     ' reached.')

        self.loadbalancer_stack.wait_for_active_loadbalancer()

        LOG.debug(f'Load Balancer {self.loadbalancer_stack.loadbalancer_id} is'
                  f' ACTIVE')

        # Wait for Octavia objects' provisioning status to be ACTIVE
        self.listener_stack.wait_for_active_members()

        # Verify Octavia functionality
        octavia.check_members_balanced(
            pool_id=self.listener_stack.pool_id,
            ip_address=self.loadbalancer_stack.floating_ip_address,
            lb_algorithm=self.listener_stack.lb_algorithm,
            protocol=self.listener_stack.lb_protocol,
            port=self.listener_stack.lb_port)
