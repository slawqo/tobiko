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
from tobiko.openstack import heat
from tobiko.tests.scenario.neutron import base
from tobiko.shell import ping


CONF = config.CONF


class FloatingIPFixture(heat.HeatStackFixture):
    template = base.heat_template_file('floating_ip.yaml')

    # template parameters
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


class FloatingIPTest(base.NeutronTest):
    """Tests server connectivity"""

    floating_ip_fixture = FloatingIPFixture

    @classmethod
    def setUpClass(cls):
        super(FloatingIPTest, cls).setUpClass()
        stack = tobiko.setup_fixture(cls.floating_ip_fixture)
        outputs = stack.wait_for_outputs()
        cls.floating_ip_address = outputs.floating_ip_address
        cls.mtu = stack.internal_network.mtu

    def test_ping(self):
        ping.ping_until_received(self.floating_ip_address).assert_replied()

    def test_ping_with_mtu_packet(self):
        ping.ping_until_received(self.floating_ip_address,
                                 packet_size=self.mtu,
                                 fragmentation=False).assert_replied()

    def test_ping_with_oversized_packet(self):
        # Wait for VM to get ready
        ping.ping_until_received(self.floating_ip_address)

        # Send 5 over-sized packets
        ping.ping(self.floating_ip_address, packet_size=self.mtu + 1,
                  fragmentation=False, count=5,
                  check=False).assert_not_replied()


class FloatingIPWithPortSecurityFixture(FloatingIPFixture):
    port_security_enabled = True


class FloatingIPWithPortSecurityTest(base.NeutronTest):
    floating_ip_fixture = FloatingIPFixture
    floating_ip_with_securtity_fixture = FloatingIPWithPortSecurityFixture

    @classmethod
    def setUpClass(cls):
        super(FloatingIPWithPortSecurityTest, cls).setUpClass()

        # Setup VM with port security
        stack = tobiko.setup_fixture(cls.floating_ip_with_securtity_fixture)
        outputs = stack.wait_for_outputs()
        cls.floating_ip_address_with_security = outputs.floating_ip_address

        # Setup VM without port security
        stack = tobiko.setup_fixture(cls.floating_ip_fixture)
        outputs = stack.wait_for_outputs()
        cls.floating_ip_address = outputs.floating_ip_address

    def test_ping(self):
        ping.ping_until_received(self.floating_ip_address).assert_replied()
        ping.ping(self.floating_ip_address_with_security,
                  count=5).assert_not_replied()


class FloatingIPWithSecurityGroupFixture(FloatingIPWithPortSecurityFixture):
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


class FloatingIPWithSecurityGroupTest(FloatingIPTest):
    floating_ip_fixture = FloatingIPWithSecurityGroupFixture
