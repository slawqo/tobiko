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
from tobiko.openstack import topology
from tobiko.shell import ssh


class LocalDockerClientTest(testtools.TestCase):

    sudo = False

    @property
    def ssh_client(self) -> ssh.SSHClientType:
        for ssh_client in self.iter_ssh_clients():
            if docker.is_docker_running(ssh_client=ssh_client,
                                        sudo=self.sudo):
                return ssh_client
        tobiko.skip_test('Docker not installed')

    @staticmethod
    def iter_ssh_clients():
        yield False

    def test_get_docker_client(self):
        client = docker.get_docker_client(ssh_client=self.ssh_client,
                                          sudo=self.sudo)
        self.assertIsInstance(client, docker.DockerClientFixture)

    def test_connect_docker_client(self):
        client = docker.get_docker_client(ssh_client=self.ssh_client,
                                          sudo=self.sudo).connect()
        self.assertIsInstance(client, docker_client.DockerClient)
        client.ping()

    def test_list_docker_containers(self):
        client = docker.get_docker_client(ssh_client=self.ssh_client,
                                          sudo=self.sudo)
        for container in docker.list_docker_containers(
                client=client):
            self.assertIsInstance(container, containers.Container)


class SShDockerClientTest(LocalDockerClientTest):

    sudo = True

    @staticmethod
    def iter_ssh_clients():
        ssh_client = ssh.ssh_proxy_client()
        if isinstance(ssh_client, ssh.SSHClientFixture):
            yield ssh_client

        nodes = topology.list_openstack_nodes()
        for node in nodes:
            if isinstance(node.ssh_client, ssh.SSHClientFixture):
                yield ssh_client
