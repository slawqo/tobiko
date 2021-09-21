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

from oslo_log import log
import pytest
import testtools

import tobiko
from tobiko import config
from tobiko.openstack import stacks


CONF = config.CONF
LOG = log.getLogger(__name__)


class RebootTrunkServerStackFixture(stacks.UbuntuServerStackFixture):
    pass


class TrunkTest(testtools.TestCase):
    """Tests trunk functionality"""

    stack = tobiko.required_fixture(RebootTrunkServerStackFixture)

    vlan_proxy_stack = tobiko.required_fixture(
        stacks.VlanProxyServerStackFixture)

    @property
    def vlan_proxy_ssh_client(self):
        return self.vlan_proxy_stack.ssh_client

    def test_activate_server(self):
        self.stack.ensure_server_status('ACTIVE')
        self.stack.assert_is_reachable()
        self.stack.assert_vlan_is_reachable(ip_version=4)

    def test_shutoff_server(self):
        self.stack.ensure_server_status('SHUTOFF')
        self.stack.assert_is_unreachable()
        self.stack.assert_vlan_is_unreachable(ip_version=4)

    @pytest.mark.ovn_migration
    def test_shutoff_then_activate_server(self):
        self.test_shutoff_server()
        self.test_activate_server()
