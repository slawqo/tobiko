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
import netaddr

import tobiko
from tobiko.shell import sh


LOG = log.getLogger(__name__)
CURL_OPTIONS = "-f --connect-timeout 2 -g"


def request(client_stack, ip_address, protocol, port, ssh_client=None):
    ssh_client = ssh_client or client_stack.ssh_client

    if netaddr.IPAddress(ip_address) == 6:
        ip_address = f"[{ip_address}]"

    cmd = f"curl {CURL_OPTIONS} {protocol.lower()}://{ip_address}:{port}/id"

    return sh.ssh_execute(ssh_client, cmd).stdout


def check_members_balanced(pool_stack, client_stack,
                           members_count,
                           loadbalancer_vip, loadbalancer_protocol,
                           loadbalancer_port, ssh_client=None):

    """Check if traffic is properly balanced between members."""

    test_case = tobiko.get_test_case()

    replies = {}

    for _ in range(members_count * 10):
        content = request(
            client_stack, loadbalancer_vip,
            loadbalancer_protocol, loadbalancer_port, ssh_client)

        if content not in replies:
            replies[content] = 0
        replies[content] += 1

        # wait one second (required when using cirros' nc fake webserver)
        time.sleep(1)

    LOG.debug("Replies from load balancer: {}".format(replies))

    # assert that 'members_count' servers replied
    test_case.assertEqual(members_count, len(replies),
                          'The number of detected active members:{} is not '
                          'as expected:{}'.format(len(replies), members_count))

    if pool_stack.lb_algorithm == 'ROUND_ROBIN':
        # assert that requests have been fairly dispatched (each server
        # received the same number of requests)
        test_case.assertEqual(1, len(set(replies.values())),
                              'The number of requests served by each member is'
                              ' different and not as expected by used '
                              'ROUND_ROBIN algorithm.')
