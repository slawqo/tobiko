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
import tobiko.common.utils.network as net_utils
from tobiko.common import exceptions


def assert_ping(ip, should_fail=False, mtu=None, fragmentation=True):
    if not net_utils.ping_ip_address(
            ip, mtu=mtu, fragmentation=fragmentation) and not should_fail:
        raise exceptions.PingException("IP address is not reachable: %s" % ip)
    elif net_utils.ping_ip_address(
            ip, mtu=mtu, fragmentation=fragmentation) and should_fail:
        raise exceptions.PingException("IP address is reachable: %s" % ip)
