# Copyright (c) 2020 Red Hat, Inc.
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

import time

from oslo_log import log
import testtools

import tobiko
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.openstack import nova
from tobiko.openstack import stacks


LOG = log.getLogger(__name__)


class RebootHostStack(stacks.CirrosServerStackFixture):
    """Server to be rebooted"""


class RebootHostTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(RebootHostStack)

    def test_reboot_host(self, nova_reboot=False, **params):
        server = self.stack.ensure_server_status('ACTIVE')
        self.assertEqual('ACTIVE', server.status)

        ssh_client = self.stack.ssh_client
        uptime_0 = sh.get_uptime(ssh_client=ssh_client)
        LOG.debug("Testing reboot command on remote host: "
                  "uptime=%r", uptime_0)
        boottime_0 = time.time() - uptime_0

        # Wait for CirrOS init script to terminate before rebooting the VM
        sh.wait_for_processes(command='^{.*}',
                              ssh_client=ssh_client,
                              timeout=90.)

        reboot = sh.reboot_host(ssh_client=ssh_client, **params)
        self.assertIs(ssh_client, reboot.ssh_client)
        self.assertEqual(ssh_client.hostname, reboot.hostname)
        method = params.get('method') or sh.soft_reset_method
        self.assertIs(method, reboot.method)

        if not reboot.is_rebooted:
            self.assert_is_not_connected(ssh_client)
            if nova_reboot:
                ping.ping_until_unreceived(self.stack.ip_address)
                nova.reboot_server(server)
            reboot.wait_for_operation()

        self.assertTrue(reboot.is_rebooted)
        self.assert_is_connected(ssh_client)

        server = nova.wait_for_server_status(self.stack.server_id, 'ACTIVE')
        self.assertEqual('ACTIVE', server.status)

        uptime_1 = sh.get_uptime(ssh_client=ssh_client)
        boottime_1 = time.time() - uptime_1
        LOG.debug("Reboot operation executed on remote host: "
                  "uptime=%r", uptime_1)
        self.assertGreater(boottime_1, boottime_0)

    def test_reboot_host_with_chash_method(self):
        self.test_reboot_host(method=sh.crash_method,
                              wait=False,
                              nova_reboot=True)

    def test_reboot_host_with_hard_method(self):
        self.test_reboot_host(method=sh.hard_reset_method)

    def test_reboot_host_with_soft_method(self):
        self.test_reboot_host(method=sh.soft_reset_method)

    def test_reboot_host_with_invalid_method(self):
        self.assertRaises(TypeError,
                          sh.reboot_host,
                          ssh_client=self.stack.ssh_client,
                          method='<invalid-method>')

    def test_reboot_host_with_wait(self):
        self.test_reboot_host(wait=True)

    def test_reboot_host_with_no_wait(self):
        self.test_reboot_host(wait=False)

    def test_reboot_server_when_shutoff(self):
        server = self.stack.ensure_server_status('SHUTOFF')
        self.assertEqual('SHUTOFF', server.status)

        ssh_client = self.stack.ssh_client
        self.assert_is_not_connected(ssh_client)
        self.assertRaises(sh.RebootHostTimeoutError,
                          sh.reboot_host,
                          ssh_client=ssh_client,
                          timeout=5.0)
        self.assert_is_not_connected(ssh_client)
        server = nova.get_server(self.stack.server_id)
        self.assertEqual('SHUTOFF', server.status)

    def assert_is_connected(self, ssh_client):
        self.assertIsNotNone(ssh_client.client)

    def assert_is_not_connected(self, ssh_client):
        self.assertIsNone(ssh_client.client)
