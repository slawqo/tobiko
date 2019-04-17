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
from tobiko.shell import ping
from tobiko.openstack import heat
from tobiko.openstack import neutron
from tobiko.tests import base
from tobiko.tests.scenario.neutron import stacks


CONF = config.CONF


class FloatingIPFixture(heat.HeatStackFixture):
    template = stacks.heat_template_file('floating_ip.yaml')

    # --- template parameters ---
    floating_network = CONF.tobiko.neutron.floating_network
    image = CONF.tobiko.nova.image
    flavor = CONF.tobiko.nova.flavor

    @property
    def internal_network(self):
        return self.internal_network_stack.outputs.network_id

    # --- required fixtures ---

    internal_network_stack = tobiko.required_setup_fixture(
        stacks.InternalNetworkFixture)

    # --- class parameters ---

    port_security_enabled = False
    security_groups = None

    def setup_parameters(self):
        super(FloatingIPFixture, self).setup_parameters()
        if self.port_security_enabled:
            self.setup_port_security()

    @neutron.skip_if_missing_networking_extensions('port-security')
    def setup_port_security(self):
        self.parameters.update(
            port_security_enabled=self.port_security_enabled,
            security_groups=self.security_groups or [])

    # --- outputs ---

    @property
    def floating_ip_address(self):
        return self.outputs.floating_ip_address

    @property
    def internal_network_mtu(self):
        return self.internal_network_stack.outputs.mtu


class FloatingIPTest(base.TobikoTest):
    """Tests server connectivity"""

    floating_ip_stack = tobiko.required_setup_fixture(FloatingIPFixture)

    def setUp(self):
        super(FloatingIPTest, self).setUp()
        stack = self.floating_ip_stack
        self.floating_ip_address = stack.floating_ip_address
        self.internal_network_mtu = stack.internal_network_mtu

    def test_ping(self):
        ping.ping_until_received(self.floating_ip_address).assert_replied()

    @neutron.skip_if_missing_networking_extensions('net-mtu')
    def test_ping_with_mtu(self):
        ping.ping_until_received(self.floating_ip_address,
                                 packet_size=self.internal_network_mtu,
                                 fragmentation=False).assert_replied()

        # Send 5 over-sized packets
        ping.ping(self.floating_ip_address,
                  packet_size=self.internal_network_mtu + 1,
                  fragmentation=False, count=5,
                  check=False).assert_not_replied()


@neutron.skip_if_missing_networking_extensions('port-security')
class FloatingIPWithPortSecurityFixture(FloatingIPFixture):
    port_security_enabled = True


class FloatingIPWithPortSecurityTest(base.TobikoTest):
    floating_ip_stack = tobiko.required_setup_fixture(FloatingIPFixture)
    floating_ip_with_securtity_stack = tobiko.required_setup_fixture(
        FloatingIPWithPortSecurityFixture)

    def setUp(self):
        super(FloatingIPWithPortSecurityTest, self).setUp()

        # Setup VM with port security
        self.floating_ip_address_with_security = (
            self.floating_ip_with_securtity_stack.outputs.floating_ip_address)

        # Setup VM without port security
        self.floating_ip_address = (
            self.floating_ip_stack.outputs.floating_ip_address)

    def test_ping(self):
        ping.ping_until_received(self.floating_ip_address).assert_replied()
        ping.ping(self.floating_ip_address_with_security,
                  count=5, check=False).assert_not_replied()


class FloatingIPWithSecurityGroupFixture(FloatingIPWithPortSecurityFixture):
    security_groups_stack = tobiko.required_setup_fixture(
        stacks.SecurityGroupsFixture)

    @property
    def security_groups(self):
        return [self.security_groups_stack.outputs.icmp_security_group_id]


class FloatingIPWithSecurityGroupTest(FloatingIPTest):
    floating_ip_stack = tobiko.required_setup_fixture(
        FloatingIPWithSecurityGroupFixture)


class FloatingIPWithNetMtuWritableFixture(FloatingIPFixture):
    internal_network_stack = tobiko.required_setup_fixture(
        stacks.InternalNetworkWithNetMtuWritableFixture)


class FlatingIpWithMtuWritableTest(FloatingIPTest):
    floating_ip_stack = tobiko.required_setup_fixture(
        FloatingIPWithNetMtuWritableFixture)
