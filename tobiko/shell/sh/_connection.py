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
import io
import os.path
import shutil
import socket
import tempfile
import typing

import paramiko
from oslo_log import log

import tobiko
from tobiko.shell.sh import _command
from tobiko.shell.sh import _exception
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _hostname
from tobiko.shell.sh import _mktemp
from tobiko.shell import ssh


LOG = log.getLogger(__name__)

ShellConnectionType = typing.Union['ShellConnection', ssh.SSHClientType, str]


def connection_hostname(connection: ShellConnectionType = None) -> str:
    return shell_connection(connection).hostname


def connection_login(connection: ShellConnectionType = None) -> str:
    return shell_connection(connection).login


def connection_username(connection: ShellConnectionType = None) -> str:
    return shell_connection(connection).username


def is_local_connection(connection: ShellConnectionType = None) -> bool:
    return shell_connection(connection).is_local


def is_cirros_connection(connection: ShellConnectionType = None) -> bool:
    return shell_connection(connection).is_cirros


def get_file(remote_file: str,
             local_file: str,
             connection: ShellConnectionType = None):
    return shell_connection(connection).get_file(
        remote_file=remote_file, local_file=local_file)


def open_file(filename: typing.Union[str, bytes],
              mode: str,
              buffering: int = None,
              connection: ShellConnectionType = None,
              sudo=False) \
            -> typing.Union[typing.IO, paramiko.sftp_file.SFTPFile]:
    connection = shell_connection(connection)
    if sudo:
        if 'r' not in mode:
            raise ValueError('sudo only supported in reading mode')
        temp_file = connection.make_temp_file(auto_clean=True)
        connection.execute(['cp', filename, temp_file], sudo=True)
        filename = temp_file
    return connection.open_file(filename=filename,
                                mode=mode,
                                buffering=buffering)


def put_file(local_file: str,
             remote_file: str,
             connection: ShellConnectionType = None):
    return shell_connection(connection).put_file(
        local_file=local_file, remote_file=remote_file)


def put_files(*local_files: str,
              remote_dir: str,
              connection: ShellConnectionType = None):
    return shell_connection(connection).put_files(*local_files,
                                                  remote_dir=remote_dir)


def make_temp_file(auto_clean=True,
                   connection: ShellConnectionType = None) -> str:
    return shell_connection(connection).make_temp_file(
        auto_clean=auto_clean)


def make_temp_dir(auto_clean=True,
                  sudo: bool = None,
                  connection: ShellConnectionType = None) -> str:
    return shell_connection(connection).make_temp_dir(
        auto_clean=auto_clean, sudo=sudo)


def remove_files(filename: str, *filenames: str,
                 connection: ShellConnectionType = None) -> str:
    return shell_connection(connection).remove_files(
        filename, *filenames)


def make_dirs(name: str,
              exist_ok=True,
              connection: ShellConnectionType = None) -> str:
    return shell_connection(connection).make_dirs(
        name=name, exist_ok=exist_ok)


def local_shell_connection() -> 'LocalShellConnection':
    return tobiko.get_fixture(LocalShellConnection)


def shell_connection(obj: ShellConnectionType = None,
                     manager: 'ShellConnectionManager' = None) \
        -> 'ShellConnection':
    if isinstance(obj, ShellConnection):
        return obj
    else:
        return shell_connection_manager(manager).get_shell_connection(obj)


def ssh_shell_connection(obj: ShellConnectionType = None,
                         manager: 'ShellConnectionManager' = None) \
        -> 'SSHShellConnection':
    connection = shell_connection(obj, manager=manager)
    return tobiko.check_valid_type(connection, SSHShellConnection)


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

    def __init__(self,
                 local_hostnames: typing.Iterable[str] = None):
        super(ShellConnectionManager, self).__init__()
        self._host_connections: typing.Dict['ShellConnectionKey',
                                            'ShellConnection'] = {}
        if local_hostnames is not None:
            local_hostnames = set(local_hostnames)
        self._local_hostnames = local_hostnames

    @property
    def local_hostnames(self) -> typing.Set[str]:
        if self._local_hostnames is None:
            hostname = socket.gethostname()
            self._local_hostnames = {'localhost',
                                     tobiko.get_short_hostname(hostname)}
        return self._local_hostnames

    def get_shell_connection(self,
                             obj: typing.Union[str, ssh.SSHClientType]) -> \
            'ShellConnection':
        ssh_client: typing.Optional[ssh.SSHClientFixture]
        if isinstance(obj, str):
            if obj in self.local_hostnames:
                ssh_client = None  # local connection
            else:
                ssh_client = ssh.ssh_client(host=obj)
        else:
            ssh_client = ssh.ssh_client_fixture(obj)
        connection = self._host_connections.get(ssh_client)
        if connection is None:
            connection = self._get_shell_connection(ssh_client=ssh_client)
            self._host_connections[ssh_client] = connection
        return connection

    def register_shell_connection(self, connection: 'ShellConnection'):
        ssh_client = ssh.ssh_client_fixture(connection.ssh_client)
        self._host_connections[ssh_client] = connection

    @staticmethod
    def _get_shell_connection(ssh_client: ssh.SSHClientFixture = None) \
            -> 'ShellConnection':
        if ssh_client is None:
            return local_shell_connection()
        else:
            return SSHShellConnection(ssh_client=ssh_client)


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

    def get_config_path(self, path: str) -> str:
        raise NotImplementedError

    def execute(self,
                command: _command.ShellCommandType,
                *args, **execute_params) -> \
            _execute.ShellExecuteResult:
        execute_params.setdefault('ssh_client', self.ssh_client)
        return _execute.execute(command, *args, **execute_params)

    def put_file(self, local_file: str, remote_file: str):
        raise NotImplementedError

    def put_files(self,
                  *local_files: str,
                  remote_dir: str,
                  make_dirs=True):
        # pylint: disable=redefined-outer-name
        remote_dir = os.path.normpath(remote_dir)
        put_files = {}
        for local_file in local_files:
            local_file = os.path.normpath(local_file)
            if os.path.isdir(local_file):
                top_dir = os.path.dirname(local_file)
                for local_dir, _, files in os.walk(local_file):
                    for filename in files:
                        local_file = os.path.join(local_dir, filename)
                        remote_file = os.path.join(
                            remote_dir,
                            os.path.relpath(local_file, start=top_dir))
                        put_files[os.path.realpath(local_file)] = remote_file
            else:
                remote_file = os.path.join(
                    remote_dir, os.path.basename(local_file))
                put_files[os.path.realpath(local_file)] = remote_file
        remote_dirs = set()
        for local_file, remote_file in sorted(put_files.items()):
            if make_dirs:
                remote_dir = os.path.dirname(remote_file)
                if remote_dir not in remote_dirs:
                    self.make_dirs(remote_dir, exist_ok=True)
                    remote_dirs.add(remote_dir)
            self.put_file(local_file, remote_file)

    def get_file(self, remote_file: str, local_file: str):
        raise NotImplementedError

    def get_environ(self) -> typing.Dict[str, str]:
        raise NotImplementedError

    def open_file(self,
                  filename: typing.Union[str, bytes],
                  mode: str,
                  buffering: int = None) \
            -> typing.Union[typing.IO, paramiko.sftp_file.SFTPFile]:
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{type(self).__name__}<{self.login}>"

    def exists(self, path: str) -> bool:
        raise NotImplementedError

    def is_file(self, path: str) -> bool:
        raise NotImplementedError

    def is_directory(self, path: str) -> bool:
        raise NotImplementedError

    def make_temp_file(self, auto_clean=True) -> str:
        raise NotImplementedError

    def make_temp_dir(self, auto_clean=True, sudo: bool = None) -> str:
        raise NotImplementedError

    def remove_files(self, filename: str, *filenames: str):
        raise NotImplementedError

    def make_dirs(self, name: str, exist_ok=True):
        raise NotImplementedError


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

    def get_environ(self) -> typing.Dict[str, str]:
        return dict(os.environ)

    def put_file(self, local_file: str, remote_file: str):
        LOG.debug(f"Copy local file as {self.login}: '{local_file}' -> "
                  f"'{remote_file}' ...")
        shutil.copyfile(local_file, remote_file)

    def get_file(self, remote_file: str, local_file: str):
        LOG.debug(f"Copy local file as {self.login}: '{remote_file}' -> "
                  f"'{local_file}' ...")
        if local_file.startswith('~'):
            local_file = os.path.expanduser(local_file)
        if remote_file.startswith('~'):
            remote_file = os.path.expanduser(remote_file)
        shutil.copyfile(remote_file, local_file)

    def open_file(self,
                  filename: typing.Union[str, bytes],
                  mode: str,
                  buffering: int = None) -> typing.IO:
        params: typing.Dict[str, typing.Any] = {}
        if buffering is not None:
            params.update(buffering=buffering)
        return io.open(file=filename, mode=mode, **params)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def is_file(self, path: str) -> bool:
        return os.path.isfile(path)

    def is_directory(self, path: str) -> bool:
        return os.path.isdir(path)

    def make_temp_file(self, auto_clean=True) -> str:
        fd, temp_file = tempfile.mkstemp()
        os.close(fd)
        if auto_clean:
            tobiko.add_cleanup(self.remove_files, temp_file)
        return temp_file

    def make_temp_dir(self, auto_clean=True, sudo: bool = None) -> str:
        if sudo:
            return _mktemp.make_temp_dir(ssh_client=self.ssh_client,
                                         sudo=True)
        else:
            temp_dir = tempfile.mkdtemp()
            LOG.debug(f"Local temporary directory created as {self.login}: "
                      f"{temp_dir}")
            if auto_clean:
                tobiko.add_cleanup(self.remove_files, temp_dir)
            return temp_dir

    def remove_files(self, filename: str, *filenames: str):
        filenames = (filename,) + filenames
        LOG.debug(f"Remove local files as {self.login}: {filenames}")
        for filename in filenames:
            if os.path.isdir(filename):
                shutil.rmtree(filename)
            elif os.path.exists(filename):
                os.remove(filename)

    def make_dirs(self, name: str, exist_ok=True):
        os.makedirs(name=name,
                    exist_ok=exist_ok)

    def get_config_path(self, path: str) -> str:
        return tobiko.tobiko_config_path(path)


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
        return self.ssh_client.setup_connect_parameters()['username']

    _hostname: typing.Optional[str] = None

    @property
    def hostname(self) -> str:
        if self._hostname is None:
            self._hostname = _hostname.ssh_hostname(ssh_client=self.ssh_client)
        return self._hostname

    _sftp: typing.Optional[paramiko.SFTPClient] = None

    @property
    def sftp_client(self) -> paramiko.SFTPClient:
        if self._sftp is None:
            self._sftp = self.ssh_client.connect().open_sftp()
        return self._sftp

    def get_environ(self) -> typing.Dict[str, str]:
        lines = self.execute('source /etc/profile; env').stdout.splitlines()
        return dict(_parse_env_line(line)
                    for line in lines
                    if line.strip())

    def put_file(self, local_file: str, remote_file: str):
        LOG.debug(f"Put remote file as {self.login}: '{local_file}' -> "
                  f"'{remote_file}'...")
        self.sftp_client.put(local_file, remote_file)

    def open_file(self,
                  filename: typing.Union[str, bytes],
                  mode: str,
                  buffering: int = None) -> paramiko.sftp_file.SFTPFile:
        if buffering is None:
            buffering = -1
        return self.sftp_client.open(filename=filename,
                                     mode=mode,
                                     bufsize=buffering)

    def get_file(self, remote_file: str, local_file: str):
        LOG.debug(f"Get remote file as {self.login}: '{remote_file}' -> "
                  f"'{local_file}'...")
        if local_file.startswith('~'):
            local_file = os.path.expanduser(local_file)
        if remote_file.startswith('~'):
            remote_file = self.execute(f'echo {remote_file}').stdout.strip()
        self.sftp_client.get(remote_file, local_file)

    def exists(self, path: str) -> bool:
        try:
            self.execute(['test', '-e', path])
        except _exception.ShellCommandFailed:
            return False
        else:
            return True

    def is_file(self, path: str) -> bool:
        try:
            self.execute(['test', '-f', path])
        except _exception.ShellCommandFailed:
            return False
        else:
            return True

    def is_directory(self, path: str) -> bool:
        try:
            self.execute(['test', '-d', path])
        except _exception.ShellCommandFailed:
            return False
        else:
            return True

    def make_temp_file(self, auto_clean=True) -> str:
        temp_file = self.execute('mktemp').stdout.strip()
        LOG.debug(f"Remote temporary file created as {self.login}: "
                  f"{temp_file}")
        if auto_clean:
            tobiko.add_cleanup(self.remove_files, temp_file)
        return temp_file

    def make_temp_dir(self, auto_clean=True, sudo: bool = None) -> str:
        temp_dir = self.execute('mktemp -d', sudo=sudo).stdout.strip()
        LOG.debug(f"Remote temporary directory created as {self.login}: "
                  f"{temp_dir}")
        if auto_clean:
            tobiko.add_cleanup(self.remove_files, temp_dir)
        return temp_dir

    def remove_files(self, filename: str, *filenames: str):
        filenames = (filename,) + filenames
        LOG.debug(f"Remove remote files as {self.login}: {filenames}")
        command = _command.shell_command('rm -fR') + filenames
        self.execute(command)

    def make_dirs(self, name: str, exist_ok=True):
        command = _command.shell_command('mkdir')
        if exist_ok:
            command += '-p'
        command += name
        self.execute(command)

    _user_dir: typing.Optional[str] = None

    @property
    def user_dir(self) -> str:
        if self._user_dir is None:
            self._user_dir = self.execute('sh -c "echo $HOME"').stdout.strip()
        return self._user_dir

    def get_config_path(self, path: str) -> str:
        if path[0] in '~.':
            path = f"{self.user_dir}{path[1:]}"
        return path


def _parse_env_line(line: str) -> typing.Tuple[str, str]:
    name, value = line.split('=', 1)
    return name.strip(), value.strip()
