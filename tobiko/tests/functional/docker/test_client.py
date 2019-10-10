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

import testtools

from docker import client as docker_client
from docker.models import containers

from tobiko import docker
from tobiko.openstack import topology


class DockerClientTest(testtools.TestCase):

    ssh_client = None

    def setUp(self):
        super(DockerClientTest, self).setUp()
        for node in topology.list_openstack_nodes(group='controller'):
            self.ssh_client = ssh_client = node.ssh_client
            break
        else:
            self.skip('Any controller node found from OpenStack topology')

        if not docker.is_docker_running(ssh_client=ssh_client):
            self.skip('Docker server is not running')

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
