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

import time

from oslo_log import log

from tobiko.shell import ssh
from tobiko.shell import sh
from tobiko.tests import base
from tobiko.tests.scenario.octavia.exceptions import RequestException

LOG = log.getLogger(__name__)
CURL_OPTIONS = "-f --connect-timeout 2 -g"


class Validators(base.TobikoTest):

    def request(self, client_stack, server_ip_address, protocol, server_port):
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

    def check_members_balanced(self, pool_stack, client_stack,
                               members_count,
                               loadbalancer_vip, loadbalancer_protocol,
                               loadbalancer_port):

        """Check if traffic is properly balanced between members."""

        replies = {}

        for _ in range(members_count * 10):
            content = self.request(
                client_stack, loadbalancer_vip,
                loadbalancer_protocol, loadbalancer_port)

            if content not in replies:
                replies[content] = 0
            replies[content] += 1

            # wait one second (required when using cirros' nc fake webserver)
            time.sleep(1)

        LOG.debug("Replies from load balancer: {}".format(replies))

        # assert that 'members_count' servers replied
        self.assertEqual(members_count, len(replies),
                         'The number of detected active members:{} is not '
                         'as expected:{}'.format(len(replies), members_count))

        if pool_stack.lb_algorithm == 'ROUND_ROBIN':
            # assert that requests have been fairly dispatched (each server
            # received the same number of requests)
            self.assertEqual(1, len(set(replies.values())),
                             'The number of requests served by each member is '
                             'different and not as expected by used '
                             'ROUND_ROBIN algorithm.')
