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

import os

import netaddr
import testtools

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.shell import ping


class KeyPairTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(stacks.KeyPairStackFixture)

    def test_key_files(self):
        self.assertTrue(os.path.isfile(self.stack.key_file))
        self.assertTrue(os.path.isfile(self.stack.key_file + '.pub'))


@keystone.skip_unless_has_keystone_credentials()
class ClientTest(testtools.TestCase):

    #: Stack of resources with a server attached to a floating IP
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    @nova.skip_if_missing_hypervisors(count=1)
    def test_list_hypervisors(self):
        hypervisor = nova.list_hypervisors().first
        self.assertIsInstance(hypervisor.id, int)
        self.assertTrue(hypervisor.hypervisor_hostname)
        netaddr.IPAddress(hypervisor.host_ip)

    @nova.skip_if_missing_hypervisors(count=1)
    def test_list_hypervisors_without_details(self):
        hypervisor = nova.list_hypervisors(detailed=False).first
        self.assertIsInstance(hypervisor.id, int)
        self.assertTrue(hypervisor.hypervisor_hostname)
        self.assertFalse(hasattr(hypervisor, 'host_ip'))

    @nova.skip_if_missing_hypervisors(count=1)
    def test_list_hypervisors_with_hypervisor_hostname(self):
        hypervisor1 = nova.list_hypervisors().first
        hypervisor2 = nova.list_hypervisors(
            hypervisor_hostname=hypervisor1.hypervisor_hostname).unique
        self.assertEqual(hypervisor1, hypervisor2)

    @nova.skip_if_missing_hypervisors(count=1)
    def test_find_hypervisor(self):
        hypervisor = nova.find_hypervisor()
        self.assertIsNotNone(hypervisor)

    @nova.skip_if_missing_hypervisors(count=2)
    def test_find_hypervisor_with_unique(self):
        self.assertRaises(tobiko.MultipleObjectsFound, nova.find_hypervisor,
                          unique=True)

    @nova.skip_if_missing_hypervisors(count=2)
    def test_find_hypervisor_without_unique(self):
        hypervisor = nova.find_hypervisor()
        self.assertIsNotNone(hypervisor)

    def test_get_console_output(self):
        output = nova.get_console_output(server=self.stack.server_id,
                                         length=50,
                                         timeout=60.)
        self.assertTrue(output)

    def test_list_servers(self):
        server_id = self.stack.server_id
        for server in nova.list_servers():
            if server_id == server.id:
                break
        else:
            self.fail('Server {} not found'.format(server_id))

    def test_find_server(self):
        server_id = self.stack.server_id
        server = nova.find_server(id=server_id, unique=True)
        self.assertEqual(server_id, server.id)

    def test_wait_for_server_status(self):
        server_id = self.stack.server_id
        server = nova.wait_for_server_status(server=server_id, status='ACTIVE')
        self.assertEqual(server_id, server.id)
        self.assertEqual('ACTIVE', server.status)

    def test_shutof_and_activate_server(self):
        server_id = self.useFixture(stacks.CirrosServerStackFixture(
            stack_name=self.id())).server_id

        server = nova.wait_for_server_status(server=server_id, status='ACTIVE')
        self.assertEqual(server_id, server.id)
        self.assertEqual('ACTIVE', server.status)

        server = nova.shutoff_server(server=server_id)
        self.assertEqual(server_id, server.id)
        self.assertEqual('SHUTOFF', server.status)

        server = nova.activate_server(server=server_id)
        self.assertEqual(server_id, server.id)
        self.assertEqual('ACTIVE', server.status)


@keystone.skip_unless_has_keystone_credentials()
class HypervisorTest(testtools.TestCase):

    def test_skip_if_missing_hypervisors(self, count=1, should_skip=False,
                                         **params):
        if should_skip:
            expected_exeption = self.skipException
        else:
            expected_exeption = self.failureException

        @nova.skip_if_missing_hypervisors(count=count, **params)
        def method():
            raise self.fail('Not skipped')

        exception = self.assertRaises(expected_exeption, method)
        if should_skip:
            hypervisors = nova.list_hypervisors(**params)
            message = "missing {!r} hypervisor(s)".format(
                count - len(hypervisors))
            if params:
                message += " with {!s}".format(
                    ','.join('{!s}={!r}'.format(k, v)
                             for k, v in params.items()))
            self.assertEqual(message, str(exception))
        else:
            self.assertEqual('Not skipped', str(exception))

    def test_skip_if_missing_hypervisors_with_no_hypervisors(self):
        self.test_skip_if_missing_hypervisors(id=-1,
                                              should_skip=True)

    def test_skip_if_missing_hypervisors_with_big_count(self):
        self.test_skip_if_missing_hypervisors(count=1000000,
                                              should_skip=True)


@keystone.skip_unless_has_keystone_credentials()
class ServiceTest(testtools.TestCase):

    def test_wait_for_services_up(self):
        nova.wait_for_services_up()


class MigrateServerStack(stacks.CirrosServerStackFixture):
    pass


@keystone.skip_unless_has_keystone_credentials()
@nova.skip_if_missing_hypervisors(count=2)
class MigrateServerTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(MigrateServerStack)

    def test_migrate_server(self):
        """Tests cold migration actually changes hypervisor
        """
        server = self.setup_server()
        initial_hypervisor = nova.get_server_hypervisor(server)

        server = self.migrate_server(server)

        final_hypervisor = nova.get_server_hypervisor(server)
        self.assertNotEqual(initial_hypervisor, final_hypervisor)

    def test_migrate_server_with_host(self):
        """Tests cold migration actually ends on target hypervisor
        """
        server = self.setup_server()
        initial_hypervisor = nova.get_server_hypervisor(server)
        for hypervisor in nova.list_hypervisors(status='enabled', state='up'):
            if initial_hypervisor != hypervisor.hypervisor_hostname:
                target_hypervisor = hypervisor.hypervisor_hostname
                break
        else:
            self.skip("Cannot find a valid hypervisor host to migrate server "
                      "to")

        server = self.migrate_server(server=server, host=target_hypervisor)

        final_hypervisor = nova.get_server_hypervisor(server)
        self.assertEqual(target_hypervisor, final_hypervisor)

    def setup_server(self):
        server = self.stack.ensure_server_status('ACTIVE')
        self.assertEqual('ACTIVE', server.status)
        return server

    def migrate_server(self, server, **params):
        self.assertEqual('ACTIVE', server.status)
        nova.migrate_server(server, **params)

        server = nova.wait_for_server_status(server, 'VERIFY_RESIZE')
        self.assertEqual('VERIFY_RESIZE', server.status)
        nova.confirm_resize(server)

        server = nova.wait_for_server_status(
            server, 'ACTIVE', transient_status={'VERIFY_RESIZE'})
        self.assertEqual('ACTIVE', server.status)

        ping.assert_reachable_hosts([self.stack.ip_address])
        return server
