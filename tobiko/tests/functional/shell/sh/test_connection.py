# Copyright (c) 2022 Red Hat, Inc.
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

import getpass
import socket

import testtools

import tobiko
from tobiko.openstack import stacks
from tobiko.openstack import topology
from tobiko.shell import sh
from tobiko.shell import ssh


class LocalShellConnectionTest(testtools.TestCase):

    @property
    def ssh_client(self) -> ssh.SSHClientType:
        return False

    @property
    def connection(self) -> sh.ShellConnection:
        return sh.shell_connection(ssh_client=self.ssh_client)

    connection_class = sh.LocalShellConnection

    def test_shell_connection(self):
        connection = sh.shell_connection(ssh_client=self.ssh_client)
        self.assertIsInstance(connection, self.connection_class)
        self.assertIs(self.connection, connection)

    @property
    def is_local(self) -> bool:
        return True

    def test_is_local(self):
        self.assertIs(self.is_local, self.connection.is_local)

    def test_is_local_connection(self):
        is_local = sh.is_local_connection(ssh_client=self.ssh_client)
        self.assertIs(self.is_local, is_local)

    @property
    def hostname(self) -> str:
        return socket.gethostname()

    def test_hostname(self):
        self.assertEqual(self.hostname, self.connection.hostname)

    def test_connection_hostname(self):
        hostname = sh.connection_hostname(ssh_client=self.ssh_client)
        self.assertEqual(self.hostname, hostname)

    @property
    def login(self) -> str:
        return f"{self.username}@{self.hostname}"

    def test_login(self):
        self.assertEqual(self.login, self.connection.login)

    def test_connection_login(self):
        login = sh.connection_login(ssh_client=self.ssh_client)
        self.assertEqual(self.login, login)

    @property
    def username(self) -> str:
        return getpass.getuser()

    def test_username(self):
        self.assertEqual(self.username, self.connection.username)

    def test_connection_username(self):
        username = sh.connection_username(ssh_client=self.ssh_client)
        self.assertEqual(self.username, username)

    @property
    def is_cirros(self) -> bool:
        return False

    def test_is_cirros(self):
        self.assertIs(self.is_cirros, self.connection.is_cirros)

    def test_is_cirros_connection(self):
        is_cirros = sh.is_cirros_connection(ssh_client=self.ssh_client)
        self.assertIs(self.is_cirros, is_cirros)


class SSHShellConnectionTest(LocalShellConnectionTest):
    connection_class = sh.SSHShellConnection

    @property
    def ssh_client(self) -> ssh.SSHClientFixture:
        ssh_client = ssh.ssh_proxy_client()
        if isinstance(ssh_client, ssh.SSHClientFixture):
            return ssh_client

        nodes = topology.list_openstack_nodes()
        for node in nodes:
            if isinstance(node.ssh_client, ssh.SSHClientFixture):
                return node.ssh_client

        return tobiko.setup_fixture(
            stacks.UbuntuMinimalServerStackFixture).ssh_client

    @property
    def is_local(self) -> bool:
        return False

    @property
    def hostname(self) -> str:
        return sh.get_hostname(ssh_client=self.ssh_client)

    @property
    def username(self) -> str:
        return self.ssh_client.username


class CirrosShellConnectionTest(SSHShellConnectionTest):

    connection_class = stacks.CirrosShellConnection

    stack = tobiko.required_fixture(stacks.CirrosServerStackFixture)

    @property
    def ssh_client(self) -> ssh.SSHClientFixture:
        return self.stack.ssh_client

    @property
    def is_cirros(self) -> bool:
        return True
