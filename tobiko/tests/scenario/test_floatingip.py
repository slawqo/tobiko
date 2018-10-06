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
from tobiko.tests.scenario import base


class FloatingIPTest(base.ScenarioTestsBase):
    """Tests server connectivity"""

    def test_pre_fip(self):
        """Validates connectivity to a server created by another test."""

        # Get floating IP address
        stack = self.stackManager.get_stack(stack_name="scenario")
        server_fip = stack.outputs[0]['output_value']

        # Check if instance is reachable
        if not self.ping_ip_address(server_fip):
            self.fail("IP address is not reachable: %s" % server_fip)

    def test_post_fip(self):
        """Validates connectivity to a server post upgrade."""

        # Get floating IP address
        stack = self.stackManager.get_stack(stack_name="scenario")
        server_fip = stack.outputs[0]['output_value']

        # Check if instance is reachable
        if not self.ping_ip_address(server_fip):
            self.fail("IP address is not reachable: %s" % server_fip)
