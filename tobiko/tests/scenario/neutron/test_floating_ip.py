# Copyright (c) 2019 Red Hat
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
from tobiko import config
from tobiko.common.utils import network
from tobiko.openstack import heat
from tobiko.tests.scenario.neutron import base


CONF = config.CONF


class FloatingIPFixture(heat.HeatStackFixture):
    template = base.heat_template_file('floating_ip.yaml')
    floating_network = CONF.tobiko.neutron.floating_network
    image = CONF.tobiko.nova.image
    flavor = CONF.tobiko.nova.flavor
    internal_network_fixture = base.InternalNetworkFixture
    internal_network = None

    def setup_parameters(self):
        super(FloatingIPFixture, self).setup_parameters()
        self.setup_internal_network()
        self.parameters['internal_network'] = self.internal_network.network_id

    def setup_internal_network(self):
        self.internal_network = tobiko.setup_fixture(
            self.internal_network_fixture).wait_for_outputs()


class FloatingIPWithPortSecurityFixture(FloatingIPFixture):
    port_security_enabled = True


class FloatingIPWithSecurityGroupFixture(FloatingIPFixture):
    port_security_enabled = True
    security_groups_fixture = base.SecurityGroupsFixture
    security_groups = None

    def setup_parameters(self):
        super(FloatingIPWithSecurityGroupFixture, self).setup_parameters()
        self.setup_security_groups()
        self.parameters['security_groups'] = [
            self.security_groups.icmp_security_group_id]

    def setup_security_groups(self):
        self.security_groups = tobiko.setup_fixture(
                self.security_groups_fixture).wait_for_outputs()


class FloatingIPTest(base.NeutronTest):
    """Tests server connectivity"""

    def test_ping_floating_ip(self, fixture_type=FloatingIPFixture):
        """Validates connectivity to a server post upgrade."""
        stack = self.setup_fixture(fixture_type)
        network.assert_ping(stack.outputs.floating_ip_address)

    def test_ping_floating_ip_with_port_security(
            self, fixture_type=FloatingIPWithPortSecurityFixture):
        """Validates connectivity to a server post upgrade."""
        stack = self.setup_fixture(fixture_type)
        network.assert_ping(stack.outputs.floating_ip_address,
                            should_fail=True)

    def test_ping_floating_ip_with_security_group(
            self, fixture_type=FloatingIPWithSecurityGroupFixture):
        """Validates connectivity to a server post upgrade."""
        stack = self.setup_fixture(fixture_type)
        network.assert_ping(stack.outputs.floating_ip_address)

    def test_ping_with_oversize_packet(self, fixture_type=FloatingIPFixture):
        stack = self.setup_fixture(fixture_type)
        network.assert_ping(stack.outputs.floating_ip_address,
                            packet_size=stack.internal_network.mtu + 1,
                            fragmentation=False, should_fail=True)
