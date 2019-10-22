# Copyright (c) 2019 Red Hat, Inc.
#
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

import tobiko
from tobiko.shell.ping import _ping


def assert_reachable_ips(target_ips, **params):
    unreachable_ips = get_unreachable_ips(target_ips, **params)
    if unreachable_ips:
        tobiko.fail("Unable to reach IP address(es): {!r}", unreachable_ips)


def get_reachable_ips(target_ips, **params):
    return tobiko.select(address
                         for address in target_ips
                         if _ping.ping(address, **params).received)


def get_unreachable_ips(target_ips, **params):
    reachable_ips = get_reachable_ips(target_ips, **params)
    return tobiko.select(address
                         for address in target_ips
                         if address not in reachable_ips)
