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
import typing

import tobiko
from tobiko.shell.sh import _command
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _hostname
from tobiko.shell import ssh


def connection_hostname(ssh_client: ssh.SSHClientType = None) -> str:
    return shell_connection(ssh_client=ssh_client).hostname


def connection_login(ssh_client: ssh.SSHClientType = None) -> str:
    return shell_connection(ssh_client=ssh_client).login


def connection_username(ssh_client: ssh.SSHClientType = None) -> str:
    return shell_connection(ssh_client=ssh_client).username


def is_local_connection(ssh_client: ssh.SSHClientType = None) -> bool:
    return shell_connection(ssh_client=ssh_client).is_local


def is_cirros_connection(ssh_client: ssh.SSHClientType = None) -> bool:
    return shell_connection(ssh_client=ssh_client).is_cirros


def shell_connection(ssh_client: ssh.SSHClientType = None,
                     manager: 'ShellConnectionManager' = None) -> \
        'ShellConnection':
    return shell_connection_manager(manager).get_shell_connection(
        ssh_client=ssh_client)


def register_shell_connection(connection: 'ShellConnection',
                              manager: 'ShellConnectionManager' = None) -> \
        None:
    tobiko.check_valid_type(connection, ShellConnection)
    shell_connection_manager(manager).register_shell_connection(connection)


def shell_connection_manager(manager: 'ShellConnectionManager' = None):
    if manager is None:
        return tobiko.setup_fixture(ShellConnectionManager)
    else:
        tobiko.check_valid_type(manager, ShellConnectionManager)
        return manager


ShellConnectionKey = typing.Optional[ssh.SSHClientFixture]


class ShellConnectionManager(tobiko.SharedFixture):

    def __init__(self):
        super(ShellConnectionManager, self).__init__()
        self._host_connections: typing.Dict['ShellConnectionKey',
                                            'ShellConnection'] = {}

    def get_shell_connection(self,
                             ssh_client: ssh.SSHClientType) -> \
            'ShellConnection':
        ssh_client = ssh.ssh_client_fixture(ssh_client)
        connection = self._host_connections.get(ssh_client)
        if connection is None:
            connection = self._setup_shell_connection(ssh_client=ssh_client)
            self._host_connections[ssh_client] = connection
        return connection

    def register_shell_connection(self, connection: 'ShellConnection'):
        ssh_client = ssh.ssh_client_fixture(connection.ssh_client)
        self._host_connections[ssh_client] = connection

    @staticmethod
    def _setup_shell_connection(ssh_client: ssh.SSHClientFixture = None) \
            -> 'ShellConnection':
        if ssh_client is None:
            return tobiko.setup_fixture(LocalShellConnection)
        else:
            return tobiko.setup_fixture(SSHShellConnection(
                ssh_client=ssh_client))


class ShellConnection(tobiko.SharedFixture):

    def connect(self) -> 'ShellConnection':
        return tobiko.setup_fixture(self)

    def close(self) -> 'ShellConnection':
        return tobiko.cleanup_fixture(self)

    def reconnect(self):
        return tobiko.reset_fixture(self)

    @property
    def hostname(self) -> str:
        raise NotImplementedError

    @property
    def ssh_client(self) -> ssh.SSHClientType:
        raise NotImplementedError

    @property
    def is_local(self) -> bool:
        raise NotImplementedError

    @property
    def is_cirros(self) -> bool:
        return False

    @property
    def username(self) -> str:
        raise NotImplementedError

    @property
    def login(self) -> str:
        return f"{self.username}@{self.hostname}"

    def execute(self,
                command: _command.ShellCommandType,
                *args, **execute_params) -> \
            _execute.ShellExecuteResult:
        execute_params.setdefault('ssh_client', self.ssh_client)
        return _execute.execute(command, *args, **execute_params)

    def __str__(self) -> str:
        return f"{type(self).__name__}<{self.login}>"


class LocalShellConnection(ShellConnection):

    @property
    def ssh_client(self) -> bool:
        return False

    @property
    def is_local(self) -> bool:
        return True

    @property
    def username(self) -> str:
        return getpass.getuser()

    @property
    def hostname(self) -> str:
        return socket.gethostname()


class SSHShellConnection(ShellConnection):

    def __init__(self,
                 ssh_client: ssh.SSHClientFixture = None):
        super().__init__()
        self._ssh_client = ssh_client

    def setup_fixture(self):
        self._ssh_client.connect()

    def cleanup_fixture(self):
        self._ssh_client.close()

    @property
    def ssh_client(self) -> ssh.SSHClientFixture:
        if self._ssh_client is None:
            raise ValueError('Unspecified SSH client')
        return self._ssh_client

    @property
    def is_local(self) -> bool:
        return False

    @property
    def username(self) -> str:
        return self.ssh_client.username

    _hostname: typing.Optional[str] = None

    @property
    def hostname(self) -> str:
        if self._hostname is None:
            self._hostname = _hostname.ssh_hostname(ssh_client=self.ssh_client)
        return self._hostname
