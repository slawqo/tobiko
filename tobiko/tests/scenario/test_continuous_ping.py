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
import tobiko.common.net_utils as net_utils


class ContinuousPingTest(base.ScenarioTestsBase):
    """Tests server connectivity over time."""

    def test_pre_continuous_ping(self):
        """Starts the ping process."""

        # Get floating IP address
        stack = self.stackManager.get_stack(stack_name="scenario")
        server_fip = stack.outputs[0]['output_value']

        # Check if instance is reachable
        if not self.ping_ip_address(server_fip):
            self.fail("IP address is not reachable: %s" % server_fip)

        # Start ping process
        net_utils.run_background_ping(server_fip)

    def test_post_continuous_ping(self):
        """Validates the ping test was successful."""

        # Get floating IP address
        stack = self.stackManager.get_stack(stack_name="scenario")
        server_fip = stack.outputs[0]['output_value']

        packet_loss = net_utils.get_packet_loss(server_fip)

        self.assertLessEqual(int(packet_loss), 5)
