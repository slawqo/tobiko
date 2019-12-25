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

import six

# We need to ignore this code under py2
# it's not compatible and parser will failed even if we use
# the `unittest.skipIf` decorator, because during the test discovery
# stestr and unittest will load this test
# module before running it and it will load podman
# too which isn't compatible in version leather than python 3
# Also the varlink mock module isn't compatible with py27, is using
# annotations syntaxe to generate varlink interface for the mocked service
# and it will raise related exceptions too.
# For all these reasons we can't run podman tests under a python 2 environment
if six.PY3:
    from podman import client as podman_client
    from podman.libs import containers

    from tobiko import podman
    from tobiko.openstack import topology

    class PodmanClientTest(testtools.TestCase):

        ssh_client = None

        def setUp(self):
            super(PodmanClientTest, self).setUp()
            for node in topology.list_openstack_nodes(group='controller'):
                self.ssh_client = ssh_client = node.ssh_client
                break
            else:
                self.skip('Any controller node found from OpenStack topology')

            if not podman.is_podman_running(ssh_client=ssh_client):
                self.skip('Podman server is not running')

        def test_get_podman_client(self):
            client = podman.get_podman_client(ssh_client=self.ssh_client)
            self.assertIsInstance(client, podman.PodmanClientFixture)

        def test_connect_podman_client(self):
            client = podman.get_podman_client(
                ssh_client=self.ssh_client).connect()
            podman_clients_valid_types = (
                podman_client.LocalClient,
                podman_client.RemoteClient
            )
            self.assertIsInstance(client, podman_clients_valid_types)
            client.ping()

        def test_list_podman_containers(self):
            podman_containers_list = podman.list_podman_containers(
                    ssh_client=self.ssh_client)
            self.assertTrue(podman_containers_list)
            for container in podman_containers_list:
                self.assertIsInstance(container, containers.Container)
