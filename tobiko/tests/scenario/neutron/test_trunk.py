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
from tobiko.openstack import nova
from tobiko.openstack import stacks


CONF = config.CONF
LOG = log.getLogger(__name__)


class CentosRebootTrunkServerStackFixture(
        stacks.CentosTrunkServerStackFixture):
    pass


class CentosTrunkTest(testtools.TestCase):
    """Tests trunk functionality"""

    stack = tobiko.required_fixture(CentosRebootTrunkServerStackFixture)

    @pytest.mark.ovn_migration
    def test_after_server_reboot(self):
        self.shutoff_server()
        self.activate_server()

    def test_after_server_shutoff(self):
        self.activate_server()
        self.shutoff_server()

    def activate_server(self) -> nova.NovaServer:
        server = self.stack.ensure_server_status('ACTIVE')
        self.stack.assert_is_reachable()
        return server

    def shutoff_server(self) -> nova.NovaServer:
        server = self.stack.ensure_server_status('SHUTOFF')
        self.stack.assert_is_unreachable()
        return server
