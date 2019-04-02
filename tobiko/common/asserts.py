# Copyright 2018 Red Hat
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

import tobiko.common.utils.network as net_utils
from tobiko.common import exceptions


class PingFailed(exceptions.TobikoException,
                 testtools.TestCase.failureException):
    message = "Failed pinging %(destination)r: %(reason)s"


def assert_ping(ip, should_fail=False, fragmentation=True,
                packet_size=None):
    success = net_utils.ping_ip_address(ip, mtu=packet_size,
                                        fragmentation=fragmentation)
    if success:
        if should_fail:
            raise PingFailed(destination=ip, reason="IP address is reachable")
    elif not should_fail:
        raise PingFailed(destination=ip, reason="IP address is not reachable")
