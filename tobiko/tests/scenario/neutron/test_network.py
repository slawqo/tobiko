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
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.shell import ping
from tobiko.shell import sh


class NetworkTest(testtools.TestCase):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosPeerServerStackFixture)

    def test_stack_create_complete(self):
        self.stack.key_pair_stack.wait_for_create_complete()
        self.stack.network_stack.wait_for_create_complete()
        self.stack.peer_stack.wait_for_create_complete()
        self.stack.wait_for_create_complete()

    def test_ssh(self):
        """Test SSH connectivity to floating IP address"""
        hostname = sh.get_hostname(ssh_client=self.stack.ssh_client)
        self.assertEqual(self.stack.server_name.lower(), hostname)

    def test_ping(self):
        """Test ICMP connectivity to floating IP address"""
        ping.ping_until_received(
            self.stack.ip_address,
            ssh_client=self.stack.peer_stack.ssh_client).assert_replied()

    # --- test l3_ha extension ------------------------------------------------

    @neutron.skip_if_missing_networking_extensions('l3-ha')
    def test_l3_ha(self):
        """Test 'mtu' network attribute"""
        gateway = self.stack.network_stack.gateway_details
        self.assertEqual(self.stack.network_stack.ha,
                         gateway['ha'])


@tobiko.skip("The test is not able to allocate required resources")
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


@tobiko.skip("The test is not able to allocate required resources")
@nova.skip_if_missing_hypervisors(count=2, state='up', status='enabled')
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


# --- l3-ha extension VM to VM scenario ---------------------------------------

@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class L3haNetworkTest(NetworkTest):
    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.L3haPeerServerStackFixture)


@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class L3haSameHostNetworkTest(SameHostNetworkTest):
    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(
        stacks.L3haSameHostServerStackFixture)


@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class L3haDifferentHostNetworkTest(DifferentHostNetworkTest):
    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(
        stacks.L3haDifferentHostServerStackFixture)
