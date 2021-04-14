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
from tobiko import tripleo
from tobiko.tests.functional.openstack import test_topology


@tripleo.skip_if_missing_undercloud
class TripleoTopologyTest(test_topology.OpenStackTopologyTest):

    topology = tobiko.required_setup_fixture(tripleo.TripleoTopology)

    def test_undercloud_group(self):
        ssh_client = tripleo.undercloud_ssh_client()
        name = sh.get_hostname(ssh_client=ssh_client).split('.')[0]
        node = self.topology.get_node(name)
        self.assertIs(node.ssh_client, ssh_client)
        self.assertEqual(name, node.name)
        nodes = self.topology.get_group('undercloud')
        self.assertEqual([node], nodes)

    @tripleo.skip_if_missing_overcloud
    def test_overcloud_group(self):
        for server in tripleo.list_overcloud_nodes():
            ssh_client = tripleo.overcloud_ssh_client(server.name)
            name = sh.get_hostname(ssh_client=ssh_client).split('.')[0]
            node = self.topology.get_node(name)
            self.assertIs(node.ssh_client, ssh_client)
            self.assertEqual(name, node.name)
            groups = ['overcloud']
            group = name.split('-', 1)[0]
            if group != name:
                groups.append(group)
            for group in groups:
                nodes = self.topology.get_group(group)
                self.assertIn(node, nodes)
                self.assertIn(group, node.groups)
            host_config = tripleo.overcloud_host_config(name)
            self.assertEqual(host_config.hostname,
                             str(node.public_ip))
