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

import time

from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack import keystone
from tobiko.openstack import octavia
from tobiko.openstack import stacks
from tobiko.shell import ssh
from tobiko.shell import sh
from tobiko.tests import base


LOG = log.getLogger(__name__)

CONF = config.CONF

CURL_OPTIONS = "-f --connect-timeout 2 -g"


class OctaviaOtherServerStackFixture(
        stacks.OctaviaServerStackFixture):
    pass


class OctaviaOtherMemberServerStackFixture(
        stacks.OctaviaMemberServerStackFixture):
    server_stack = tobiko.required_setup_fixture(
        OctaviaOtherServerStackFixture)


class RequestException(tobiko.TobikoException):
    message = ("Error while sending request to server "
               "(command was '{command}'): {error}")


class TimeoutException(tobiko.TobikoException):
    message = "Timeout exception: {reason}"


@keystone.skip_if_missing_service(name='octavia')
class OctaviaBasicTrafficScenarioTest(base.TobikoTest):
    """Octavia traffic scenario test.

    Create a load balancer with 2 members that run a server application,
    Create a client that is connected to the load balancer VIP port,
    Generate network traffic from the client to the load balanacer.
    """
    loadbalancer_stack = tobiko.required_setup_fixture(
        stacks.OctaviaLoadbalancerStackFixture)

    listener_stack = tobiko.required_setup_fixture(
        stacks.OctaviaListenerStackFixture)

    member1_stack = tobiko.required_setup_fixture(
        stacks.OctaviaMemberServerStackFixture)

    member2_stack = tobiko.required_setup_fixture(
        OctaviaOtherMemberServerStackFixture)

    client_stack = tobiko.required_setup_fixture(
        stacks.OctaviaClientServerStackFixture)

    members_count = 2

    def setUp(self):
        # pylint: disable=no-member
        super(OctaviaBasicTrafficScenarioTest, self).setUp()

        # Wait for members
        self._check_member(self.member1_stack)
        self._check_member(self.member2_stack)

        # Check if load balancer is functional
        self._check_loadbalancer()

    def _request(self, client_stack, server_ip_address, protocol, server_port):
        """Perform a request on a server.

        Returns the response in case of success, throws an RequestException
        otherwise.
        """
        if ':' in server_ip_address:
            # Add square brackets around IPv6 address to please curl
            server_ip_address = "[{}]".format(server_ip_address)
        cmd = "curl {} {}://{}:{}/id".format(
            CURL_OPTIONS, protocol.lower(), server_ip_address, server_port)

        ssh_client = ssh.ssh_client(
            client_stack.floating_ip_address,
            username=client_stack.image_fixture.username)

        ret = sh.ssh_execute(ssh_client, cmd)
        if ret.exit_status != 0:
            raise RequestException(command=cmd,
                                   error=ret.stderr)

        return ret.stdout

    def _wait_resource_operating_status(self, resource_type, operating_status,
                                        resource_get, *args):
        start = time.time()

        while time.time() - start < CONF.tobiko.octavia.check_timeout:
            res = resource_get(*args)
            if res['operating_status'] == operating_status:
                return

            time.sleep(CONF.tobiko.octavia.check_interval)

        raise TimeoutException(
            reason=("Cannot get operating_status '{}' from {} {} "
                    "within the timeout period.".format(
                        operating_status, resource_type, args)))

    def _wait_lb_operating_status(self, lb_id, operating_status):
        LOG.debug("Wait for loadbalancer {} to have '{}' "
                  "operating_status".format(lb_id, operating_status))
        self._wait_resource_operating_status("loadbalancer",
                                             operating_status,
                                             octavia.get_loadbalancer,
                                             lb_id)

    def _wait_for_request_data(self, client_stack, server_ip_address,
                               server_protocol, server_port):
        """Wait until a request on a server succeeds

        Throws a TimeoutException after CONF.tobiko.octavia.check_timeout
        if the server doesn't reply.
        """
        start = time.time()

        while time.time() - start < CONF.tobiko.octavia.check_timeout:
            try:
                ret = self._request(client_stack, server_ip_address,
                                    server_protocol, server_port)
            except Exception as e:
                LOG.warning("Received exception {} while performing a "
                            "request".format(e))
            else:
                return ret
            time.sleep(CONF.tobiko.octavia.check_interval)

        raise TimeoutException(
            reason=("Cannot get data from {} on port {} with "
                    "protocol {} within the timeout period.".format(
                        server_ip_address, server_port,
                        server_protocol)))

    def _check_loadbalancer(self):
        """Wait until the load balancer is functional."""

        # Check load balancer status
        loadbalancer_id = self.loadbalancer_stack.loadbalancer_id
        self._wait_lb_operating_status(loadbalancer_id, 'ONLINE')

        loadbalancer_vip = self.loadbalancer_stack.loadbalancer_vip
        loadbalancer_port = self.listener_stack.lb_port
        loadbalancer_protocol = self.listener_stack.lb_protocol

        self._wait_for_request_data(self.client_stack,
                                    loadbalancer_vip,
                                    loadbalancer_protocol,
                                    loadbalancer_port)

    def _check_member(self, member_stack):
        """Wait until a member server is functional."""

        member_ip = member_stack.server_stack.floating_ip_address
        member_port = member_stack.application_port
        member_protocol = self.listener_stack.pool_protocol

        self._wait_for_request_data(self.client_stack, member_ip,
                                    member_protocol, member_port)

    def _check_members_balanced(self):
        """Check if traffic is properly balanced between members."""
        replies = {}

        loadbalancer_vip = self.loadbalancer_stack.loadbalancer_vip
        loadbalancer_port = self.listener_stack.lb_port
        loadbalancer_protocol = self.listener_stack.lb_protocol

        for _ in range(20):
            content = self._request(self.client_stack, loadbalancer_vip,
                                    loadbalancer_protocol, loadbalancer_port)

            if content not in replies:
                replies[content] = 0
            replies[content] += 1

            # wait one second (required when using cirros' nc fake webserver)
            time.sleep(1)

        LOG.debug("Replies from load balancer: {}".format(
            replies))

        # assert that 'members_count' servers replied
        self.assertEqual(len(replies), self.members_count)

        if self.listener_stack.lb_algorithm == 'ROUND_ROBIN':
            # assert that requests have been fairly dispatched (each server
            # received the same number of requests)
            self.assertEqual(len(set(replies.values())), 1)

    def test_traffic(self):
        self._check_members_balanced()
