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
import os
import re
import signal
import subprocess

from tobiko.tests.scenario import base


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

        ping_log = open("/tmp/ping_%s_output" % server_fip, 'ab')
        p = subprocess.Popen(['ping -q 8.8.8.8'], stdout=ping_log, shell=True)
        with open("/tmp/ping_%s_pid" % server_fip, 'ab') as pf:
            pf.write(str(p.pid))

    def test_post_continuous_ping(self):
        """Validates the ping test was successful."""

        # Get floating IP address
        stack = self.stackManager.get_stack(stack_name="scenario")
        server_fip = stack.outputs[0]['output_value']

        # Kill Process
        with open("/tmp/ping_%s_pid" % server_fip) as f:
            pid = f.read()
        os.kill(int(pid), signal.SIGINT)

        # Packet loss pattern
        p = re.compile("(\d{1,3})% packet loss")

        # Check ping package loss
        with open("/tmp/ping_%s_output" % server_fip) as f:
            m = p.search(f.read())
            packet_loss = m.group(1)
        self.assertLessEqual(int(packet_loss), 5)

        # Remove files created by pre test
        os.remove("/tmp/ping_%s_output" % server_fip)
        os.remove("/tmp/ping_%s_pid" % server_fip)
