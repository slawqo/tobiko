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

import collections
import typing

from oslo_log import log

import tobiko
from tobiko.shell import curl
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


def check_members_balanced(members_count: int,
                           ip_address: str,
                           protocol: str,
                           port: int,
                           lb_algorithm: str = None,
                           requests_count: int = 10,
                           connect_timeout: tobiko.Seconds = 2.,
                           interval: tobiko.Seconds = 1,
                           ssh_client: ssh.SSHClientFixture = None) -> (
        typing.Dict[str, int]):

    """Check if traffic is properly balanced between members."""

    test_case = tobiko.get_test_case()

    replies: typing.Dict[str, int] = collections.defaultdict(lambda: 0)
    for attempt in tobiko.retry(count=members_count * requests_count,
                                interval=interval):
        content = curl.execute_curl(hostname=ip_address,
                                    scheme=protocol,
                                    port=port,
                                    path='id',
                                    connect_timeout=connect_timeout,
                                    ssh_client=ssh_client).strip()
        replies[content] += 1

        if attempt.is_last:
            break
    else:
        raise RuntimeError('Broken retry loop')

    LOG.debug(f"Replies counts from load balancer: {replies}")

    # assert that 'members_count' servers replied
    missing_members_count = members_count - len(replies)
    test_case.assertEqual(0, missing_members_count,
                          f'Missing replies from {missing_members_count} "'
                          '"members.')

    if lb_algorithm == 'ROUND_ROBIN':
        # assert that requests have been fairly dispatched (each server
        # received the same number of requests)
        test_case.assertEqual(1, len(set(replies.values())),
                              'The number of requests served by each member is'
                              ' different and not as expected by used '
                              'ROUND_ROBIN algorithm.')

    return replies
