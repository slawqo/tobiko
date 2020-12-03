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

from docker import client as docker_client
from docker.models import containers
import testtools

import tobiko
from tobiko import docker
from tobiko.openstack import keystone
from tobiko.openstack import topology


class DockerNodeFixture(tobiko.SharedFixture):

    node = None

    def setup_fixture(self):
        nodes = topology.list_openstack_nodes()
        for node in nodes:
            assert node.ssh_client is not None
            if docker.is_docker_running(ssh_client=node.ssh_client):
                self.node = node
                break

        if self.node is None:
            nodes_text = ' '.join(node.name for node in nodes)
            tobiko.skip_test("Docker server is not running in any of nodes "
                             f"{nodes_text}")


@keystone.skip_unless_has_keystone_credentials()
class DockerClientTest(testtools.TestCase):

    node = tobiko.required_setup_fixture(DockerNodeFixture)

    @property
    def ssh_client(self):
        return self.node.node.ssh_client

    def test_get_docker_client(self):
        client = docker.get_docker_client(ssh_client=self.ssh_client)
        self.assertIsInstance(client, docker.DockerClientFixture)

    def test_connect_docker_client(self):
        client = docker.get_docker_client(ssh_client=self.ssh_client).connect()
        self.assertIsInstance(client, docker_client.DockerClient)
        client.ping()

    def test_list_docker_containers(self):
        for container in docker.list_docker_containers(
                ssh_client=self.ssh_client):
            self.assertIsInstance(container, containers.Container)
