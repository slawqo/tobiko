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

import abc
import contextlib
import random

from oslo_log import log
import pytest
import testtools

import tobiko
from tobiko import config
from tobiko.openstack import heat
from tobiko.openstack import keystone
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.shell import ping


LOG = log.getLogger(__name__)


class CirrosServerStackFixture(stacks.CirrosServerStackFixture):

    def validate_created_stack(self):
        stack = super().validate_created_stack()
        try:
            server = nova.get_server(self.server_id)
        except nova.ServerNotFoundError as ex:
            if config.is_prevent_create():
                tobiko.skip_test(str(ex))
            else:
                raise heat.InvalidStackError(name=self.stack_name) from ex
        else:
            if server.status != 'SHUTOFF':
                if server.status != 'ACTIVE':
                    try:
                        nova.activate_server(server)
                    except nova.WaitForServerStatusTimeout as ex:
                        raise heat.InvalidStackError(
                            name=self.stack_name) from ex
                try:
                    self.assert_is_reachable()
                except ping.UnreachableHostsException as ex:
                    raise heat.InvalidStackError(name=self.stack_name) from ex

        return stack


@keystone.skip_unless_has_keystone_credentials()
class CirrosServerTest(testtools.TestCase):

    stack = tobiko.required_fixture(CirrosServerStackFixture)
    peer_stack = tobiko.required_fixture(stacks.CirrosServerStackFixture)

    @pytest.mark.server_create
    @config.skip_if_prevent_create()
    def test_0_create_server(self):
        tobiko.cleanup_fixture(type(self).stack.fixture)
        self.ensure_server(status='ACTIVE')
        self.assert_is_reachable()

    def test_1_server_name(self):
        server = self.ensure_server()
        self.assertEqual(self.stack.server_name, server.name)

    @pytest.mark.server_active
    def test_2_activate_server(self):
        self.ensure_server(status='ACTIVE')
        self.assert_is_reachable()

    @pytest.mark.server_shutoff
    def test_3_shutoff_server(self):
        self.ensure_server(status='SHUTOFF')
        self.assert_is_unreachable()

    def test_4_shutoff_and_activate_server(self):
        self.ensure_server(status='SHUTOFF')
        self.ensure_server(status='ACTIVE')
        self.assert_is_reachable()

    @pytest.mark.server_migrate
    @pytest.mark.flaky(reruns=2, reruns_delay=60)
    @nova.skip_if_missing_hypervisors(count=2)
    def test_5_migrate_server(self, live=False):
        """Tests cold migration actually changes hypervisor
        """
        server = self.ensure_server(status='ACTIVE')
        initial_hypervisor = nova.get_server_hypervisor(server)

        server = self.migrate_server(server, live=live)
        final_hypervisor = nova.get_server_hypervisor(server)
        self.assertNotEqual(initial_hypervisor, final_hypervisor)

    @pytest.mark.server_migrate
    @pytest.mark.flaky(reruns=2, reruns_delay=60)
    @nova.skip_if_missing_hypervisors(count=2)
    def test_6_live_migrate_server(self):
        self.test_5_migrate_server(live=True)

    @pytest.mark.server_migrate
    @pytest.mark.flaky(reruns=2, reruns_delay=60)
    @nova.skip_if_missing_hypervisors(count=2)
    def test_7_migrate_server_with_host(self, live=False):
        """Tests cold migration actually ends on target hypervisor
        """
        server = self.ensure_server(status='ACTIVE')
        initial_hypervisor = nova.get_server_hypervisor(server)

        hypervisors = nova.list_hypervisors(
            status='enabled', state='up').select(
            lambda h: h.hypervisor_hostname != initial_hypervisor)
        if not hypervisors:
            tobiko.skip_test("Cannot find a valid hypervisor host to migrate "
                             "server to")
        target_hypervisor = random.choice(hypervisors).hypervisor_hostname

        server = self.migrate_server(server=server,
                                     host=target_hypervisor,
                                     live=live)
        final_hypervisor = nova.get_server_hypervisor(server)
        self.assertNotEqual(initial_hypervisor, final_hypervisor)
        self.assertEqual(target_hypervisor, final_hypervisor)

    @pytest.mark.server_migrate
    @pytest.mark.flaky(reruns=2, reruns_delay=60)
    @nova.skip_if_missing_hypervisors(count=2)
    def test_8_live_migrate_server_with_host(self):
        self.test_7_migrate_server_with_host(live=True)

    @config.skip_if_prevent_create()
    @pytest.mark.server_delete
    def test_9_delete_server(self):
        server = self.ensure_server()
        self.addCleanup(self.ensure_server)
        nova.delete_server(server)
        for _ in tobiko.retry(timeout=60., interval=3.):
            try:
                server = nova.get_server(server.id)
            except nova.ServerNotFoundError:
                LOG.debug(f"Server '{server.id}' deleted")
                break
            else:
                LOG.debug(f"Waiting for server deletion:\n"
                          f" - server.id='{server.id}'"
                          f" - server.status='{server.status}'")
        self.assert_is_unreachable()

    def ensure_server(self, status: str = None):
        server_id: str = self.stack.server_id
        try:
            server = nova.find_server(id=server_id, unique=True)
        except tobiko.ObjectNotFound:
            LOG.debug(f"Server '{server_id}' not found: recreate it...")
            server_id = tobiko.reset_fixture(self.stack).server_id
            server = nova.find_server(id=server_id, unique=True)
            LOG.debug(f"Server '{server_id}' created.")
        if status not in [None, server.status]:
            LOG.debug(f"Ensuring server '{server_id}' status changes:\
                      '{server.status}' -> '{status}'")
            server = self.stack.ensure_server_status(status)
            self.assertEqual(status, server.status)
        return server

    def migrate_server(self, server, live=False, **params):
        self.assert_is_reachable()
        self.assertEqual('ACTIVE', server.status)
        if live:
            with self.handle_migration_errors():
                nova.live_migrate_server(server, **params)
            server = nova.wait_for_server_status(
                server, 'ACTIVE', transient_status=['MIGRATING'])
        else:
            with self.handle_migration_errors():
                nova.migrate_server(server, **params)
            server = nova.wait_for_server_status(server, 'VERIFY_RESIZE')
            self.assertEqual('VERIFY_RESIZE', server.status)
            nova.confirm_resize(server)
            server = nova.wait_for_server_status(
                server, 'ACTIVE', transient_status=['VERIFY_RESIZE'])
        self.assert_is_reachable()
        return server

    @contextlib.contextmanager
    def handle_migration_errors(self):
        try:
            yield
        except (nova.PreCheckMigrateServerError,
                nova.NoValidHostFoundMigrateServerError) as ex:
            self.skipTest(str(ex))

    def assert_is_reachable(self):
        self.stack.assert_is_reachable()
        ping.assert_reachable_hosts(self.stack.list_fixed_ips(),
                                    timeout=300.,
                                    ssh_client=self.peer_stack.ssh_client)
        if self.stack.has_vlan:
            self.stack.assert_vlan_is_reachable()

    def assert_is_unreachable(self):
        self.stack.assert_is_unreachable()
        ping.assert_unreachable_hosts(self.stack.list_fixed_ips(),
                                      timeout=300.,
                                      ssh_client=self.peer_stack.ssh_client)
        if self.stack.has_vlan:
            self.stack.assert_vlan_is_unreachable()


class CloudInitServerStackFixture(stacks.CloudInitServerStackFixture,
                                  abc.ABC):

    def validate_created_stack(self):
        stack = super().validate_created_stack()
        self.wait_for_cloud_init_done()
        self.assert_is_reachable()
        return stack


class UbuntuMinimalServerStackFixture(CloudInitServerStackFixture,
                                      stacks.UbuntuMinimalServerStackFixture):
    pass


@pytest.mark.flaky(reruns=2, reruns_delay=60)
class UbuntuMinimalServerTest(CirrosServerTest):
    stack = tobiko.required_fixture(UbuntuMinimalServerStackFixture)


class UbuntuServerStackFixture(CloudInitServerStackFixture,
                               stacks.UbuntuServerStackFixture):
    pass


@pytest.mark.flaky(reruns=2, reruns_delay=60)
class UbuntuServerTest(CirrosServerTest):
    stack = tobiko.required_fixture(UbuntuServerStackFixture)


class FedoraServerStackFixture(CloudInitServerStackFixture,
                               stacks.FedoraServerStackFixture):
    pass


@pytest.mark.flaky(reruns=2, reruns_delay=60)
class FedoraServerTest(CirrosServerTest):
    stack = tobiko.required_fixture(FedoraServerStackFixture)


class CentosServerStackFixture(CloudInitServerStackFixture,
                               stacks.CentosServerStackFixture):
    pass


@pytest.mark.flaky(reruns=2, reruns_delay=60)
class CentosServerTest(CirrosServerTest):
    stack = tobiko.required_fixture(CentosServerStackFixture)


class RedhatServerStackFixture(CloudInitServerStackFixture,
                               stacks.RedHatServerStackFixture):
    pass


@pytest.mark.flaky(reruns=2, reruns_delay=60)
class RedhatServerTest(CirrosServerTest):
    stack = tobiko.required_fixture(RedhatServerStackFixture)
