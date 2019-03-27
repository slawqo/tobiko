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
from tobiko.common import asserts
from tobiko.openstack import heat
from tobiko.tests.scenario.neutron import base


CONF = config.CONF


class FloatingIPFixture(heat.HeatStackFixture):
    template = base.heat_template_file('floating_ip.yaml')
    parameters = {'floating_network': CONF.tobiko.neutron.floating_network,
                  'image': CONF.tobiko.nova.image,
                  'flavor': CONF.tobiko.nova.flavor}

    def setup_parameters(self):
        super(FloatingIPFixture, self).setup_parameters()
        internal_network = tobiko.setup_fixture(
                base.InternalNetworkFixture).wait_for_outputs()
        self.parameters['internal_network'] = internal_network.network_id


class FloatingIPWithPortSecurityFixture(FloatingIPFixture):
    parameters = {'port_security_enabled': True}


class FloatingIPWithSecurityGroupFixture(FloatingIPFixture):
    parameters = {'port_security_enabled': True}

    def setup_parameters(self):
        super(FloatingIPWithSecurityGroupFixture, self).setup_parameters()
        security_groups = tobiko.setup_fixture(
                base.SecurityGroupsFixture).wait_for_outputs()
        self.parameters['security_groups'] = [
            security_groups.icmp_security_group_id]


class FloatingIPTest(base.NeutronTest):
    """Tests server connectivity"""

    def test_ping_floating_ip(self,
                              fixture_type=FloatingIPFixture,
                              should_fail=False):
        """Validates connectivity to a server post upgrade."""
        stack = tobiko.setup_fixture(fixture_type)
        outputs = stack.wait_for_outputs()
        asserts.assert_ping(outputs.floating_ip_address,
                            should_fail=should_fail)

    def test_ping_floating_ip_with_port_security(self):
        """Validates connectivity to a server post upgrade."""
        self.test_ping_floating_ip(
            fixture_type=FloatingIPWithPortSecurityFixture,
            should_fail=True)

    def test_ping_floating_ip_security_group(self):
        """Validates connectivity to a server post upgrade."""
        self.test_ping_floating_ip(
            fixture_type=FloatingIPWithSecurityGroupFixture)
