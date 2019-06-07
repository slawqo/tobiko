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

import testtools

import tobiko
from tobiko.openstack import stacks
from tobiko.shell import ping


class FloatingIPTest(testtools.TestCase):
    """Tests connectivity to Nova instances via floating IPs"""

    floating_ip_stack = tobiko.required_setup_fixture(
        stacks.FloatingIpServerStackFixture)

    @property
    def floating_ip_address(self):
        """Floating IP address"""
        return self.floating_ip_stack.outputs.floating_ip_address

    def test_ping(self):
        """Test connectivity to floating IP address"""
        ping.ping_until_received(self.floating_ip_address).assert_replied()
