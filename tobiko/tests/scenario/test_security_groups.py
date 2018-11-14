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
from tobiko.common.asserts import assert_ping
from tobiko.common.utils.network import SG_RULES
from tobiko.tests.scenario import base


class SecurityGroupTest(base.ScenarioTestsBase):
    """Tests security groups."""

    def setUp(self):
        super(SecurityGroupTest, self).setUp(__file__)
        self.stack = self._get_stack()
        self.fip = self.stackManager.get_output(self.stack, "fip")
        self.unreachable_fip = self.stackManager.get_output(self.stack, "fip2")
        self.blank_sg_id = self.stackManager.get_output(self.stack, "sg2")

    def test_pre_secgroup(self):
        """Validates security group before upgrade."""

        assert_ping(self.fip)
        assert_ping(self.unreachable_fip, should_fail=True)

    def test_post_secgroup(self):
        """Validates security groups post upgrade."""

        assert_ping(self.fip)
        assert_ping(self.unreachable_fip, should_fail=True)

        # Add 'allow ICMP' rule to the blank security group
        self.networkManager.create_sg_rules([SG_RULES['ALLOW_ICMP']],
                                            self.blank_sg_id)

        # Make sure unreachable floating IP is now reachable
        assert_ping(self.unreachable_fip)
