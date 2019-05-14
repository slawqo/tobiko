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
import socket
import time

import paramiko
from oslo_log import log

import tobiko
from tobiko.shell.paramiko import _config


LOG = log.getLogger(__name__)


SSH_CONNECT_PARAMETERS = [
    'hostname', 'port', 'username', 'password', 'pkey', 'key_filename',
    'timeout', 'allow_agent', 'look_for_keys', 'compress', 'banner_timeout',
    'auth_timeout', 'passphrase']


class SSHClientFixture(tobiko.SharedFixture):

    host = None
    username = None
    port = 22
    client = None

    paramiko_conf = tobiko.required_setup_fixture(
        _config.SSHParamikoConfFixture)
    ssh_config = tobiko.required_setup_fixture(_config.SSHConfigFixture)
    host_config = None

    proxy_client = None
    proxy_command = None
    proxy_sock = None

    def __init__(self, host=None, proxy_client=None, **connect_parameters):
        super(SSHClientFixture, self).__init__()
        if host:
            self.host = host
        if proxy_client:
            self.proxy_client = proxy_client
        invalid_parameters = sorted([
            name
            for name in connect_parameters
            if name not in SSH_CONNECT_PARAMETERS])
        if invalid_parameters:
            message = "Invalid SSH connection parameters: {!s}".format(
                ', '.join(invalid_parameters))
            raise ValueError(message)
        self.connect_parameters = connect_parameters

    def setup_fixture(self):
        self.setup_host_config()
        self.setup_connect_parameters()
        self.setup_proxy_sock()
        self.setup_ssh_client()

    def setup_host_config(self):
        host = self.host
        if not host:
            message = 'Invalid host: {!r}'.format(host)
            raise ValueError(message)
        self.host_config = self.ssh_config.lookup(host)

    def setup_connect_parameters(self):
        # Import missing parameters from below objects:
        # - self.host_config
        # - self
        missing_parameters = [name
                              for name in SSH_CONNECT_PARAMETERS
                              if self.connect_parameters.get(name) is None]
        for obj in [self.host_config, self]:
            parameters = {}
            for name in missing_parameters:
                value = getattr(obj, name, None)
                if value is not None:
                    parameters[name] = value
            if parameters:
                LOG.debug("Got connect parameters for host %r from object %r: "
                          " %r", self.host, obj, parameters)
                self.connect_parameters.update(parameters)
                missing_parameters = [name
                                      for name in missing_parameters
                                      if name not in parameters]

        hostname = self.connect_parameters.get('hostname')
        if not hostname:
            message = "Invalid hostname: {!r}".format(hostname)
            raise ValueError(message)

        key_filename = self.connect_parameters.get('key_filename')
        if key_filename:
            key_filename = os.path.expanduser(key_filename)
            if not os.path.exists(key_filename):
                message = "key_filename {!r} doesn't exist".format(hostname)
                raise ValueError(message)
            self.connect_parameters['key_filename'] = key_filename

    def setup_proxy_sock(self):
        proxy_command = (self.host_config.proxy_command or self.proxy_command)
        proxy_client = self.proxy_client
        if proxy_client:
            proxy_command = proxy_command or 'nc {hostname!r} {port!r}'
        elif not proxy_command:
            return

        parameters = self.connect_parameters
        proxy_command = proxy_command.format(
            hostname=parameters['hostname'],
            port=parameters.get('port', 22))

        if proxy_client:
            if isinstance(proxy_client, SSHClientFixture):
                # Connect to proxy server
                proxy_client = tobiko.setup_fixture(proxy_client).client

            # Open proxy channel
            LOG.debug("Execute proxy command on proxy host: %r", proxy_command)
            self.proxy_sock = proxy_client.get_transport().open_session()
            self.addCleanup(self.cleanup_proxy_sock)
            self.proxy_sock.exec_command(proxy_command)

        else:
            LOG.debug("Execute proxy command on local host: %r", proxy_command)
            self.proxy_sock = paramiko.ProxyCommand(proxy_command)
            self.addCleanup(self.cleanup_proxy_sock)

    def setup_ssh_client(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()

        now = time.time()
        timeout = now + self.connect_timeout
        sleep_time = self.connect_sleep_time
        while True:
            message = "time left {!s} seconds".format(timeout - now)
            try:
                self._connect_client(client, message=message)
                break
            except (EOFError, socket.error, socket.timeout,
                    paramiko.SSHException):
                now = time.time()
                if now + sleep_time >= timeout:
                    raise

                LOG.debug('Retry to connect to %r in %d seconds',
                          self.connect_login, sleep_time)
                time.sleep(sleep_time)
                now = time.time()
                if now >= timeout:
                    raise
                sleep_time += self.connect_sleep_time_increment

    def _connect_client(self, client, message=None):
        """Returns an ssh connection to the specified host."""
        parameters = self.connect_parameters
        extra_info = ''
        if message:
            extra_info = ' (' + message + ')'
        LOG.info("Creating SSH connection to %r%s...", self.connect_login,
                 extra_info)

        try:
            client.connect(sock=self.proxy_sock, **parameters)
        except Exception as ex:
            LOG.debug("Error connecting to  %s%s: %s", self.connect_login,
                      extra_info, ex)
            raise
        else:
            self.client = client
            self.addCleanup(self.cleanup_ssh_client, client)
            LOG.info("SSH connection to %s successfully created",
                     self.connect_login)

    def cleanup_ssh_client(self):
        if self.client:
            self.client = None
            self.client.close()

    def cleanup_proxy_sock(self):
        proxy_sock = self.proxy_sock
        if proxy_sock:
            self.proxy_sock = None
            proxy_sock.close()

    @property
    def connect_timeout(self):
        return self.paramiko_conf.connect_timeout

    @property
    def connect_sleep_time(self):
        return self.paramiko_conf.connect_sleep_time

    @property
    def connect_sleep_time_increment(self):
        return self.paramiko_conf.connect_sleep_time_increment

    @property
    def connect_login(self):
        login = self.connect_parameters['hostname']
        port = self.connect_parameters.get('port', None)
        if port:
            login = ':'.join([login, str(port)])
        username = self.connect_parameters.get('username', None)
        if username:
            login = "@".join([username, login])
        return login


class SSHClientManager(object):

    ssh_config = tobiko.required_setup_fixture(_config.SSHConfigFixture)
    paramiko_conf = tobiko.required_setup_fixture(
        _config.SSHParamikoConfFixture)

    def __init__(self):
        self.clients = {}

    def get_client(self, host, username=None, port=None, proxy_jump=None):
        host_config = self.ssh_config.lookup(host)
        hostname = host_config.hostname
        port = port or host_config.port
        username = username or host_config.username
        proxy_jump = proxy_jump or host_config.proxy_jump
        host_key = hostname, port, username, proxy_jump
        client = self.clients.get(host_key)
        if not client:
            proxy_client = None
            if proxy_jump:
                proxy_client = self.get_client(proxy_jump)
            self.clients[host_key] = client = SSHClientFixture(
                host=host, hostname=hostname, port=port, username=username,
                proxy_client=proxy_client)
        return client

    @property
    def proxy_client(self):
        proxy_jump = self.paramiko_conf.proxy_jump
        if proxy_jump:
            return self.get_client(proxy_jump)
        else:
            return None


CLIENTS = SSHClientManager()


def ssh_client(host, port=None, username=None, proxy_jump=None,
               manager=None):
    manager = manager or CLIENTS
    return manager.get_client(host=host, port=port, username=username,
                              proxy_jump=proxy_jump)


def ssh_proxy_client(manager=None):
    manager = manager or CLIENTS
    return manager.proxy_client
