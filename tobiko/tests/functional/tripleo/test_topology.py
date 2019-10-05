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

import tobiko
from tobiko.shell import sh
from tobiko.tripleo import overcloud
from tobiko.tripleo import topology
from tobiko.tripleo import undercloud
from tobiko.tests.functional.openstack import test_topology


class TripleoTopologyTest(test_topology.OpenStackTopologyTest):

    topology = tobiko.required_setup_fixture(topology.TripleoTopology)

    @undercloud.skip_if_missing_undercloud
    def test_undercloud_group(self):
        ssh_client = undercloud.undercloud_ssh_client()
        name = sh.get_hostname(ssh_client=ssh_client).split('.')[0]
        node = self.topology.get_node(name)
        self.assertIs(node.ssh_client, ssh_client)
        self.assertEqual(name, node.name)
        group = self.topology.get_group('undercloud')
        self.assertEqual([node], group.nodes)
        host_config = undercloud.undercloud_host_config()
        self.assertEqual(host_config.hostname, str(node.addresses.first))

    @overcloud.skip_if_missing_overcloud
    def test_overcloud_group(self):
        for server in overcloud.list_overcloud_nodes():
            ssh_client = overcloud.overcloud_ssh_client(server.name)
            node_name = sh.get_hostname(ssh_client=ssh_client).split('.')[0]
            node = self.topology.get_node(node_name)
            self.assertIs(node.ssh_client, ssh_client)
            self.assertEqual(node_name, node.name)
            group_names = ['overcloud']
            group_name = node_name.split('-', 1)[0]
            if group_name != node_name:
                group_names.append(group_name)
            for group_name in group_names:
                group = self.topology.get_group(group_name)
                self.assertIn(node, group.nodes)
                self.assertIn(group, node.groups)
            host_config = overcloud.overcloud_host_config(node_name)
            self.assertEqual(host_config.hostname,
                             str(node.addresses.first))
