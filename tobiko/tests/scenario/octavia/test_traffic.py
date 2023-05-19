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
from oslo_log import log

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import octavia
from tobiko.openstack import stacks
from tobiko.shell import sh


LOG = log.getLogger(__name__)


@keystone.skip_if_missing_service(name='octavia')
class OctaviaBasicTrafficScenarioTest(testtools.TestCase):
    """Octavia traffic scenario test.

    Create a load balancer with 2 members that run a server application,
    Create a client that is connected to the load balancer VIP port,
    Generate network traffic from the client to the load balanacer.
    """
    loadbalancer_stack = tobiko.required_fixture(
        stacks.AmphoraIPv4LoadBalancerStack)

    listener_stack = tobiko.required_fixture(
        stacks.HttpRoundRobinAmphoraIpv4Listener)

    def setUp(self):
        # pylint: disable=no-member
        super(OctaviaBasicTrafficScenarioTest, self).setUp()

        # Wait for Octavia objects to be active
        LOG.info('Waiting for member '
                 f'{self.listener_stack.server_stack.stack_name} and '
                 f'for member '
                 f'{self.listener_stack.other_server_stack.stack_name} '
                 f'to be created...')
        self.listener_stack.wait_for_active_members()

        self.loadbalancer_stack.wait_for_octavia_service()

        self.listener_stack.wait_for_members_to_be_reachable()

    def test_round_robin_traffic(self):
        _test_traffic(
            pool_id=self.listener_stack.pool_id,
            ip_address=self.loadbalancer_stack.floating_ip_address,
            lb_algorithm=self.listener_stack.lb_algorithm,
            protocol=self.listener_stack.lb_protocol,
            port=self.listener_stack.lb_port)


def _test_traffic(pool_id: str, ip_address: str, lb_algorithm: str,
                  protocol: str, port: int):
    # For 5 minutes we ignore specific exceptions as we know
    # that Octavia resources are being provisioned
    for attempt in tobiko.retry(timeout=300.):
        try:
            octavia.check_members_balanced(pool_id=pool_id,
                                           ip_address=ip_address,
                                           lb_algorithm=lb_algorithm,
                                           protocol=protocol,
                                           port=port)
            break

        # TODO oschwart: change the following without duplicating code
        except octavia.RoundRobinException:
            if lb_algorithm == 'ROUND_ROBIN':
                LOG.exception(f"Traffic didn't reach all members after "
                              f"#{attempt.number} attempts and "
                              f"{attempt.elapsed_time} seconds")
            if attempt.is_last:
                raise
        except (octavia.TrafficTimeoutError,
                sh.ShellCommandFailed):
            LOG.exception(f"Traffic didn't reach all members after "
                          f"#{attempt.number} attempts and "
                          f"{attempt.elapsed_time} seconds")
            if attempt.is_last:
                raise


@neutron.skip_unless_is_ovn()
@keystone.skip_if_missing_service(name='octavia')
class OctaviaOVNProviderTrafficTest(testtools.TestCase):
    """Octavia OVN provider traffic test.

    Create an OVN provider load balancer with 2 members that run a server
    application,
    Create a client that is connected to the load balancer VIP port via FIP,
    Generate TCP network traffic from the client to the load balancer FIP.
    """
    loadbalancer_stack = tobiko.required_fixture(
        stacks.OVNIPv4LoadBalancerStack)

    listener_stack = tobiko.required_fixture(
        stacks.TcpSourceIpPortOvnIpv4Listener)

    def setUp(self):
        # pylint: disable=no-member
        super(OctaviaOVNProviderTrafficTest, self).setUp()

        # Wait for Octavia objects to be active
        LOG.info(f'Waiting for member {self.listener_stack.member_id} and '
                 f'for member {self.listener_stack.other_member_id} '
                 f'to be created...')
        self.listener_stack.wait_for_active_members()

        self.loadbalancer_stack.wait_for_octavia_service()

    def test_source_ip_port_traffic(self):
        """Send traffic to the load balancer FIP to test source ip port
        """
        _test_traffic(
            pool_id=self.listener_stack.pool_id,
            ip_address=self.loadbalancer_stack.floating_ip_address,
            lb_algorithm=self.listener_stack.lb_algorithm,
            protocol=self.listener_stack.lb_protocol,
            port=self.listener_stack.lb_port)
