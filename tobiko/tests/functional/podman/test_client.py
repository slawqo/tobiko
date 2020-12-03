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

import types

import testtools

import tobiko
from tobiko import podman
from tobiko.openstack import keystone
from tobiko.openstack import topology


class PodmanNodeFixture(tobiko.SharedFixture):

    node = None

    def setup_fixture(self):
        nodes = topology.list_openstack_nodes()
        for node in nodes:
            assert node.ssh_client is not None
            if podman.is_podman_running(ssh_client=node.ssh_client):
                self.node = node
                break

        if self.node is None:
            nodes_text = ' '.join(node.name for node in nodes)
            tobiko.skip_test("Podman server is not running in any of nodes "
                             f"{nodes_text}")


@keystone.skip_unless_has_keystone_credentials()
class PodmanClientTest(testtools.TestCase):

    node = tobiko.required_setup_fixture(PodmanNodeFixture)

    @property
    def ssh_client(self):
        return self.node.node.ssh_client

    def test_get_podman_client(self):
        client = podman.get_podman_client(ssh_client=self.ssh_client)
        self.assertIsInstance(client, podman.PodmanClientFixture)

    def test_connect_podman_client(self):
        client = podman.get_podman_client(
            ssh_client=self.ssh_client).connect()
        self.assertTrue(client.system.ping())

    def test_list_podman_containers(self):
        client = podman.get_podman_client(
            ssh_client=self.ssh_client).connect()
        self.assertIsInstance(client.containers.list(),
                              types.GeneratorType)
