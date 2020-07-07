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
from tobiko import config
from tobiko.openstack import stacks
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import tests


class ServerStackResourcesTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def test_server(self):
        "Test actual server details"
        server = self.stack.resources.server
        self.assertEqual('OS::Nova::Server', server.resource_type)
        # Verify actual server status (is alive, etc.)
        nova_client = nova.get_nova_client()
        server_data = nova_client.servers.get(server.physical_resource_id)
        self.assertEqual(self.stack.server_name, server_data.name)

    def test_port(self):
        "Test actual server port details"
        port = self.stack.resources.port
        self.assertEqual('OS::Neutron::Port', port.resource_type)
        # Verify actual port status (is alive, etc.)
        port_data = neutron.get_port(port.physical_resource_id)
        self.assertEqual(port.physical_resource_id, port_data['id'])


class ServerCreationTest(testtools.TestCase):

    def setUp(self):
        testtools.TestCase.setUp(self)
        if config.get_bool_env('TOBIKO_PREVENT_CREATE'):
            self.skip('TOBIKO_PREVENT_CREATE is true')

    def test_server_creation(self):
        tests.test_server_creation()

    def test_evacuable_server_creation(self):
        tests.test_evacuable_server_creation()

    def test_server_creation_and_shutoff(self):
        tests.test_server_creation_and_shutoff()

    def test_servers_creation(self):
        tests.test_servers_creation()
