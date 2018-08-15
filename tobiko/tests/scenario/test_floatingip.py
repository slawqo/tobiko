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
        """Creates a server and checks it can reach it."""

        # Defines parameters required by heat template
        parameters = {'public_net': self.conf.floating_network_name,
                      'image': "cirros-0.3.5-x86_64-disk.img",
                      'flavor': "m1.tiny"}

        # creates stack and stores its ID
        st = self.stackManager.create_stack(stack_name="fip",
                                            template_name="fip.yaml",
                                            parameters=parameters)
        sid = st['stack']['id']

        # Before pinging the floating IP, ensure resource is ready
        self.stackManager.wait_for_status_complete(sid, 'floating_ip')

        # Get floating IP address
        stack = self.stackManager.client.stacks.get(sid)
        server_fip = stack.outputs[0]['output_value']

        # Check if instance is reachable
        if not self.ping_ip_address(server_fip):
            self.fail("IP address is not reachable: %s" % server_fip)

    def test_post_fip(self):
        """Validates connectivity to a server created by another test."""

        stack = self.stackManager.get_stack(stack_name="fip")
        server_fip = stack.outputs[0]['output_value']

        # Check if instance is reachable
        if not self.ping_ip_address(server_fip):
            self.fail("IP address is not reachable: %s" % server_fip)
