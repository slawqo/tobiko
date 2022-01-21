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

import collections
import json
import typing

import testtools
from oslo_log import log

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import octavia
from tobiko.openstack import stacks
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


@keystone.skip_if_missing_service(name='octavia')
class OctaviaBasicTrafficScenarioTest(testtools.TestCase):
    """Octavia traffic scenario test.

    Create a load balancer with 2 members that run a server application,
    Create a client that is connected to the load balancer VIP port,
    Generate network traffic from the client to the load balanacer.
    """
    loadbalancer_stack = tobiko.required_setup_fixture(
        stacks.AmphoraIPv4LoadBalancerStack)

    listener_stack = tobiko.required_setup_fixture(
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
        # For 5 minutes seconds we ignore specific exceptions as we know
        # that Octavia resources are being provisioned
        for attempt in tobiko.retry(timeout=300.):
            try:
                octavia.check_members_balanced(
                    pool_id=self.listener_stack.pool_id,
                    ip_address=self.loadbalancer_stack.floating_ip_address,
                    lb_algorithm=self.listener_stack.lb_algorithm,
                    protocol=self.listener_stack.lb_protocol,
                    port=self.listener_stack.lb_port)
                break
            except (octavia.RoundRobinException,
                    octavia.TrafficTimeoutError,
                    sh.ShellCommandFailed) as e:
                LOG.exception(f"Traffic didn't reach all members after "
                              f"#{attempt.number} attempts and "
                              f"{attempt.elapsed_time} seconds")
                if attempt.is_last:
                    raise e


@neutron.skip_unless_is_ovn()
@keystone.skip_if_missing_service(name='octavia')
class OctaviaOVNProviderTrafficTest(testtools.TestCase):
    """Octavia OVN provider traffic test.

    Create an OVN provider load balancer with 2 members that run a server
    application,
    Create a client that is connected to the load balancer VIP port via FIP,
    Generate network traffic from the client to the load balanacer via ssh.
    """
    loadbalancer_stack = tobiko.required_setup_fixture(
        stacks.OVNIPv4LoadBalancerStack)

    listener_stack = tobiko.required_setup_fixture(
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

    def test_ssh_traffic(self):
        """SSH every member server to get its hostname using a load balancer
        """
        username: typing.Optional[str] = None
        password: typing.Optional[str] = None
        missing_replies = set()

        for member_server in [self.listener_stack.server_stack,
                              self.listener_stack.other_server_stack]:
            ssh_client = member_server.ssh_client
            hostname = sh.get_hostname(ssh_client=ssh_client)
            missing_replies.add(hostname)
            if username is None:
                username = member_server.username
            else:
                self.assertEqual(username,
                                 member_server.username,
                                 "Not all member servers have the same "
                                 "username to login with")
            if password is None:
                password = member_server.password
            else:
                self.assertEqual(password, member_server.password,
                                 "Not all member servers have the same "
                                 "password to login with")

        # Get SSH client to the load balancer virtual IP
        ssh_client = ssh.ssh_client(
            host=self.loadbalancer_stack.floating_ip_address,
            port=self.listener_stack.lb_port,
            username=username,
            password=password)

        replies = []
        for attempt in tobiko.retry(timeout=120.):
            LOG.debug(f"SSH to member server by using the load balancer "
                      f"(login='{ssh_client.login}', attempt={attempt})...")

            with ssh_client:  # disconnect after every loop
                hostname = sh.ssh_hostname(ssh_client=ssh_client)
            try:
                missing_replies.remove(hostname)
            except KeyError:
                self.assertIn(hostname, replies,
                              f"Unexpected hostname reached: {hostname}")
            replies.append(hostname)
            if missing_replies:
                LOG.debug('Reached member server(s):\n'
                          f'{pretty_replies(replies)}')
                if attempt.is_last:
                    self.fail('Unreached member server(s): {missing_replies}')
                else:
                    LOG.debug('Waiting for reaching remaining server(s)... '
                              f'{missing_replies}')
            else:
                LOG.debug('All member servers reached:\n'
                          f'{pretty_replies(replies)}')
                break
        else:
            raise RuntimeError('Broken retry loop')


def pretty_replies(replies: typing.Iterable[str]):
    return json.dumps(collections.Counter(replies),
                      indent=4,
                      sort_keys=True)
