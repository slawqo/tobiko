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

from tobiko.tests.scenario import base
from tobiko.common.asserts import assert_ping


class FloatingIPTest(base.ScenarioTestsBase):
    """Tests server connectivity"""

    @classmethod
    def setUpClass(cls):
        super(FloatingIPTest, cls).setUpClass()
        cls.fip = cls.stacks.get_output(cls.stack, "fip")
        cls.unreachable_fip = cls.stacks.get_output(cls.stack, "fip2")

    def test_ping_floating_ip(self):
        """Validates connectivity to a server post upgrade."""
        assert_ping(self.fip)

    def test_ping_unreachable_floating_ip(self):
        assert_ping(self.unreachable_fip, should_fail=True)
