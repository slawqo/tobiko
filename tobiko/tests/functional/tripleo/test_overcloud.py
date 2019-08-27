# Copyright 2019 Red Hat
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

import netaddr
import testtools

import tobiko
from tobiko import config
from tobiko.shell import ping
from tobiko.tripleo import overcloud


CONF = config.CONF


@overcloud.skip_if_missing_overcloud
class OvercloudSshConnectionTest(testtools.TestCase):

    def test_fetch_overcloud_credentials(self):
        env = overcloud.load_overcloud_rcfile()
        self.assertTrue(env['OS_AUTH_URL'])
        self.assertTrue(env.get('OS_USERNAME') or env.get('OS_USER_ID'))
        self.assertTrue(env['OS_PASSWORD'])
        self.assertTrue(env.get('OS_TENANT_NAME') or
                        env.get('OS_PROJECT_NAME') or
                        env.get('OS_TENANT_ID') or
                        env.get('OS_PROJECT_ID'))


@overcloud.skip_if_missing_overcloud
class OvercloudNovaAPITest(testtools.TestCase):

    def test_list_overcloud_nodes(self):
        nodes = overcloud.list_overcloud_nodes()
        self.assertTrue(nodes)
        expected_network_name = None
        for node in nodes:
            network_name, node_ip = get_recheable_node_ip(node=node)
            self.assertTrue(node_ip)
            if expected_network_name:
                self.assertEqual(expected_network_name, network_name)
            else:
                expected_network_name = network_name

    def test_find_overcloud_nodes(self):
        node = overcloud.find_overcloud_node()
        network_name, node_ip = get_recheable_node_ip(node=node)
        self.assertTrue(network_name)
        self.assertTrue(node_ip)


def get_recheable_node_ip(node):
    for network_name, addresses in node.addresses.items():
        for address in addresses:
            ip_address = netaddr.IPAddress(address['addr'],
                                           version=address['version'])
            if ping.ping(host=ip_address).received:
                return network_name, ip_address
    tobiko.fail('Unrecheable overcloud node {!r}', node.id)
