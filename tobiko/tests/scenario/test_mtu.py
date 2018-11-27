# Copyright (c) 2018 Red Hat
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

from tempest.common import utils

from tobiko.common.asserts import assert_ping
from tobiko.tests.scenario import base

from testtools import skip


@skip("Broken or incomplete test case.")
class MTUTest(base.ScenarioTestsBase):
    """Tests MTU."""

    def setUp(self):
        super(MTUTest, self).setUp(__file__)
        self.stack = self._get_stack()
        self.fip_max_mtu = self.stackManager.get_output(
            self.stack, "fip_max_mtu")
        self.fip_min_mtu = self.stackManager.get_output(
            self.stack, "fip_min_mtu")
        self.net_max_mtu = self.networkManager.client.show_network(
            self.stackManager.get_output(self.stack, "network_max_mtu"))
        self.net_min_mtu = self.networkManager.client.show_network(
            self.stackManager.get_output(self.stack, "network_min_mtu"))

    def test_pre_mtu(self):
        """Validates MTU before upgrade."""

        # Ping without fragmentation and without changing MTU should succeed
        assert_ping(self.fip_max_mtu)
        assert_ping(self.fip_min_mtu)

        assert_ping(self.fip_min_mtu, should_fail=True,
                    mtu=self.net_min_mtu['network']['mtu'] + 100,
                    fragmentation=False)

    def test_post_mtu(self):
        """Validates MTU post upgrade."""

        # Assert ping without fragmentation still works
        assert_ping(self.fip_max_mtu)

        assert_ping(self.fip_max_mtu, should_fail=True,
                    mtu=self.net_max_mtu['network']['mtu'] + 100,
                    fragmentation=False)

    @utils.requires_ext(extension="net-mtu-writable", service="network")
    def test_post_writeable_mtu(self):
        """Validates writeable MTU post upgrade."""

        # Assert ping without fragmentation still works
        assert_ping(self.fip_min_mtu)
        assert_ping(self.fip_max_mtu)

        updated_min_mtu = self.net_min_mtu['network']['mtu'] + 100

        assert_ping(self.fip_min_mtu, should_fail=True,
                    mtu=updated_min_mtu, fragmentation=False)

        # Update MTU
        self.networkManager.client.update_network(
            self.net_min_mtu_id, body={'network': {'mtu': updated_min_mtu}})

        assert_ping(self.fip_min_mtu, should_fail=False,
                    mtu=updated_min_mtu, fragmentation=False)
