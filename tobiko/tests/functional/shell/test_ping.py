# Copyright (c) 2019 Red Hat, Inc.
#
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

import os

import netaddr
import testtools

import tobiko
from tobiko import config
from tobiko.shell import ip
from tobiko.shell import ping
from tobiko.tests.functional.shell import fixtures


CONF = config.CONF


class PingTest(testtools.TestCase):

    namespace = tobiko.required_setup_fixture(fixtures.NetworkNamespaceFixture)

    def test_ping_recheable_address(self):
        result = ping.ping('127.0.0.1', count=3)
        self.assertIsNone(result.source)
        self.assertEqual(netaddr.IPAddress('127.0.0.1'), result.destination)
        result.assert_transmitted()
        result.assert_replied()

    def test_ping_reachable_hostname(self):
        result = ping.ping('example.org', count=3)
        self.assertIsNone(result.source)
        # self.assertIsNotNone(result.destination)
        result.assert_transmitted()
        result.assert_replied()

    def test_ping_unreachable_address(self):
        result = ping.ping('1.2.3.4', count=3)
        self.assertIsNone(result.source)
        self.assertEqual(netaddr.IPAddress('1.2.3.4'), result.destination)
        result.assert_transmitted()
        result.assert_not_replied()

    def test_ping_unreachable_hostname(self):
        ex = self.assertRaises(ping.UnknowHostError, ping.ping,
                               'unreachable-host', count=3)
        if ex.details:
            self.assertEqual('unreachable-host', ex.details)

    def test_ping_until_received(self):
        result = ping.ping_until_received('127.0.0.1', count=3)
        self.assertIsNone(result.source)
        self.assertEqual(netaddr.IPAddress('127.0.0.1'), result.destination)
        result.assert_transmitted()
        result.assert_replied()

    def test_ping_until_received_unreachable(self):
        ex = self.assertRaises(ping.PingFailed, ping.ping_until_received,
                               '1.2.3.4', count=3, timeout=6)
        self.assertEqual(6, ex.timeout)
        self.assertEqual(0, ex.count)
        self.assertEqual(3, ex.expected_count)
        self.assertEqual('received', ex.message_type)

    def test_ping_until_unreceived_recheable(self):
        ex = self.assertRaises(ping.PingFailed, ping.ping_until_unreceived,
                               '127.0.0.1', count=3, timeout=6)
        self.assertEqual(6, ex.timeout)
        self.assertEqual(0, ex.count)
        self.assertEqual(3, ex.expected_count)
        self.assertEqual('unreceived', ex.message_type)

    def test_ping_until_unreceived_unrecheable(self):
        result = ping.ping_until_unreceived('1.2.3.4', count=3)
        self.assertIsNone(result.source)
        self.assertEqual(netaddr.IPAddress('1.2.3.4'), result.destination)
        result.assert_transmitted()
        result.assert_not_replied()

    def test_ping_reachable_with_timeout(self):
        ex = self.assertRaises(ping.PingFailed, ping.ping, '127.0.0.1',
                               count=20, timeout=1.)
        self.assertEqual(1., ex.timeout)
        self.assertEqual(20, ex.expected_count)
        self.assertEqual('transmitted', ex.message_type)

    def test_ping_hosts(self, ssh_client=None, network_namespace=None,
                        **params):
        if not os.path.isfile('/sbin/ip'):
            self.skip("'/sbin/ip' command not found")
        ips = ip.list_ip_addresses(ssh_client=ssh_client,
                                   network_namespace=network_namespace)
        reachable_ips, unrecheable_ips = ping.ping_hosts(
            ips, ssh_client=ssh_client, network_namespace=network_namespace,
            **params)

        expected_reachable = [i for i in ips if i in reachable_ips]
        self.assertEqual(expected_reachable, reachable_ips)
        expected_unreachable = [i for i in ips if i not in reachable_ips]
        self.assertEqual(expected_unreachable, unrecheable_ips)

    def test_ping_hosts_from_network_namespace(self):
        self.test_ping_hosts(
            ssh_client=self.namespace.ssh_client,
            network_namespace=self.namespace.network_namespace)
