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
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.openstack import tests
from tobiko.shell import ping


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


class MigrateServerStack(stacks.CirrosServerStackFixture):
    pass


@keystone.skip_unless_has_keystone_credentials()
@nova.skip_if_missing_hypervisors(count=2)
class MigrateServerTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(MigrateServerStack)
    peer_stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def test_migrate_server(self, live=False):
        """Tests cold migration actually changes hypervisor
        """
        server = self.setup_server()
        initial_hypervisor = nova.get_server_hypervisor(server)

        server = self.migrate_server(server, live=live)

        final_hypervisor = nova.get_server_hypervisor(server)
        self.assertNotEqual(initial_hypervisor, final_hypervisor)

    def test_migrate_server_with_host(self, live=False):
        """Tests cold migration actually ends on target hypervisor
        """
        server = self.setup_server()
        initial_hypervisor = nova.get_server_hypervisor(server)
        for hypervisor in nova.list_hypervisors(status='enabled', state='up'):
            if initial_hypervisor != hypervisor.hypervisor_hostname:
                target_hypervisor = hypervisor.hypervisor_hostname
                break
        else:
            target_hypervisor = None
            self.skipTest("Cannot find a valid hypervisor host to migrate "
                          "server to")

        server = self.migrate_server(server=server, host=target_hypervisor,
                                     live=live)

        final_hypervisor = nova.get_server_hypervisor(server)
        self.assertEqual(target_hypervisor, final_hypervisor)

    @tobiko.skip("Expected to create problems on compute nodes")
    def test_live_migrate_server(self):
        self.test_migrate_server(live=True)

    @tobiko.skip("Expected to create problems on compute nodes")
    def test_live_migrate_server_with_host(self):
        self.test_migrate_server_with_host(live=True)

    def setup_server(self):
        server = self.stack.ensure_server_status('ACTIVE')
        self.assertEqual('ACTIVE', server.status)
        return server

    def migrate_server(self, server, live=False, **params):
        self.assertEqual('ACTIVE', server.status)
        # wait until all VM fixed IPs are reachable
        ping.assert_reachable_hosts(self.stack.list_fixed_ips(),
                                    timeout=900.,
                                    ssh_client=self.peer_stack.ssh_client)

        if live:
            nova.live_migrate_server(server, **params)
            server = nova.wait_for_server_status(
                server, 'ACTIVE', transient_status=['MIGRATING'])
        else:
            nova.migrate_server(server, **params)

            server = nova.wait_for_server_status(server, 'VERIFY_RESIZE')
            self.assertEqual('VERIFY_RESIZE', server.status)
            nova.confirm_resize(server)

            server = nova.wait_for_server_status(
                server, 'ACTIVE', transient_status=['VERIFY_RESIZE'])
        self.assertEqual('ACTIVE', server.status)

        # wait until all VM fixed IPs are reachable
        ping.assert_reachable_hosts(self.stack.list_fixed_ips(),
                                    timeout=900.,
                                    ssh_client=self.peer_stack.ssh_client)
        # check floating IP is reachable
        ping.assert_reachable_hosts([self.stack.floating_ip_address])
        return server
