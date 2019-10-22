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

from tobiko.shell.ping import _assert
from tobiko.shell.ping import _exception
from tobiko.shell.ping import _interface
from tobiko.shell.ping import _parameters
from tobiko.shell.ping import _ping
from tobiko.shell.ping import _statistics


assert_reachable_ips = _assert.assert_reachable_ips
get_reachable_ips = _assert.get_reachable_ips
get_unreachable_ips = _assert.get_unreachable_ips

PingException = _exception.PingException
PingError = _exception.PingError
LocalPingError = _exception.LocalPingError
BadAddressPingError = _exception.BadAddressPingError
UnknowHostError = _exception.UnknowHostError
PingFailed = _exception.PingFailed

skip_if_missing_fragment_ping_option = (
    _interface.skip_if_missing_fragment_ping_option)
has_ping_fragment_option = _interface.has_fragment_ping_option

ping_parameters = _parameters.ping_parameters
get_ping_parameters = _parameters.get_ping_parameters
default_ping_parameters = _parameters.default_ping_parameters

ping = _ping.ping
ping_until_delivered = _ping.ping_until_delivered
ping_until_undelivered = _ping.ping_until_undelivered
ping_until_received = _ping.ping_until_received
ping_until_unreceived = _ping.ping_until_unreceived
TRANSMITTED = _ping.TRANSMITTED
UNDELIVERED = _ping.UNDELIVERED
DELIVERED = _ping.DELIVERED
RECEIVED = _ping.RECEIVED
UNRECEIVED = _ping.UNRECEIVED

PingStatistics = _statistics.PingStatistics
