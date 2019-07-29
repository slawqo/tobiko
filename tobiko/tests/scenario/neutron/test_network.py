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


import testtools

import tobiko
from tobiko.openstack import stacks
from tobiko.shell import sh


class NetworkTest(testtools.TestCase):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosPeerServerStackFixture)

    def test_ssh(self):
        """Test SSH connectivity to floating IP address"""
        result = sh.execute("hostname",
                            ssh_client=self.stack.ssh_client)
        hostname = result.stdout.rstrip()
        self.assertEqual(self.stack.server_name.lower(), hostname)


# --- Same compute host VM to VM scenario -------------------------------------


class SameHostNetworkTest(NetworkTest):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(
        stacks.CirrosSameHostServerStackFixture)

    def test_same_host(self):
        sender = self.stack.peer_stack.server_details
        receiver = self.stack.server_details
        self.assertEqual({'same_host': [sender.id]},
                         self.stack.scheduler_hints)
        self.assertEqual(getattr(sender, 'OS-EXT-SRV-ATTR:host'),
                         getattr(receiver, 'OS-EXT-SRV-ATTR:host'))


# --- Different compute host VM to VM scenario --------------------------------


class DifferentHostNetworkTest(NetworkTest):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(
        stacks.CirrosDifferentHostServerStackFixture)

    def test_different_host(self):
        sender = self.stack.peer_stack.server_details
        receiver = self.stack.server_details
        self.assertEqual({'different_host': [sender.id]},
                         self.stack.scheduler_hints)
        self.assertNotEqual(getattr(sender, 'OS-EXT-SRV-ATTR:host'),
                            getattr(receiver, 'OS-EXT-SRV-ATTR:host'))
