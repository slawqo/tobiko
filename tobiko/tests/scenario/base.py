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
import subprocess
from tempest.common.utils import net_utils
from tempest.lib.common.utils import test_utils

from tobiko.tests import base
from tobiko.common import stack
from tobiko.common import clients


class ScenarioTestsBase(base.TobikoTest):
    """All scenario tests inherit from this scenario base class."""

    def setUp(self):
        super(ScenarioTestsBase, self).setUp()
        self.clientManager = clients.ClientManager(self.conf)

        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.stackManager = stack.StackManager(self.clientManager,
                                               templates_dir)

    def ping_ip_address(self, ip_address, should_succeed=True,
                        ping_timeout=None, mtu=None):

        timeout = ping_timeout or 120
        cmd = ['ping', '-c1', '-w1']

        if mtu:
            cmd += [
                # don't fragment
                '-M', 'do',
                # ping receives just the size of ICMP payload
                '-s', str(net_utils.get_ping_payload_size(mtu, 4))
            ]
        cmd.append(ip_address)

        def ping():
            proc = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            proc.communicate()

            return (proc.returncode == 0) == should_succeed

        result = test_utils.call_until_true(ping, timeout, 1)
        return result
