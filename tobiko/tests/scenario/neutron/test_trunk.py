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

import pytest
import testtools

import tobiko
from tobiko import config
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.shell import ping


CONF = config.CONF


class TrunkTest(testtools.TestCase):
    """Tests trunk functionality"""

    stack = tobiko.required_setup_fixture(
        stacks.CentosTrunkServerStackFixture)

    @pytest.mark.flaky(reruns=3, reruns_delay=120)
    @pytest.mark.ovn_migration
    def test_trunk_fip_after_reboot(self):
        ping.assert_reachable_hosts([self.stack.floating_ip_address])
        server = nova.shutoff_server(self.stack.server_id)
        self.assertEqual('SHUTOFF', server.status)
        ping.assert_unreachable_hosts([self.stack.ip_address])
        server = nova.activate_server(self.stack.server_id)
        self.assertEqual('ACTIVE', server.status)
        ping.assert_reachable_hosts([self.stack.ip_address])
