# Copyright 2022 Red Hat
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

import netaddr
import testtools

from tobiko import shiftstack
from tobiko.shell import ping
from tobiko.shiftstack import stacks


@shiftstack.skip_unless_has_shiftstack()
class ShiftstackStacksTest(testtools.TestCase):

    def test_ensure_shiftstack_node_floating_ip(self):
        nodes = shiftstack.list_shiftstack_nodes(status='ACTIVE')
        floating_ips = []
        for node in nodes:
            floating_ip = stacks.ensure_shiftstack_node_floating_ip(
                server=node)
            self.assertIsInstance(floating_ip, netaddr.IPAddress)
            floating_ips.append(floating_ip)
        ping.assert_reachable_hosts(floating_ips)
