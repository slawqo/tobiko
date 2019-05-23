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


SSH_CONNECT_PARAMETERS = {
    #: The server to connect to
    'hostname': str,

    #: The server port to connect to
    'port': int,

    #: The username to authenticate as (defaults to the current local username)
    'username': str,

    #: Used for password authentication; is also used for private key
    #  decryption if passphrase is not given
    'password': str,

    #: Used for decrypting private keys
    'passphrase': str,

    #: The filename, or list of filenames, of optional private key(s) and/or
    #  certs to try for authentication
    'key_filename': str,

    #: An optional timeout (in seconds) for the TCP connect
    'timeout': float,

    #: Set to False to disable connecting to the SSH agent
    'allow_agent': bool,

    #: Set to False to disable searching for discoverable private key files in
    # ~/.ssh/
    'look_for_keys': bool,

    #: Set to True to turn on compression
    'compress': bool,

    #: True if you want to use GSS-API authentication
    'gss_auth': bool,

    #: Perform GSS-API Key Exchange and user authentication
    'gss_kex': bool,

    #: Delegate GSS-API client credentials or not
    'gss_deleg_creds': bool,

    #: The targets name in the kerberos database. default: hostname
    'gss_host': str,

    #: Indicates whether or not the DNS is trusted to securely canonicalize the
    #  name of the host being connected to (default True).
    'gss_trust_dns': bool,

    #: An optional timeout (in seconds) to wait for the SSH banner to be
    #  presented.
    'banner_timeout': float,

    #: An optional timeout (in seconds) to wait for an authentication response
    'auth_timeout': float
}


class SSHConnectFailure(tobiko.TobikoException):
    message = "Failed to login to {login}\n{cause}"


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

    connect_parameters = None

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
        self._connect_parameters = connect_parameters

    def setup_fixture(self):
        self.setup_host_config()
        self.setup_connect_parameters()
        self.setup_ssh_client()

    def setup_host_config(self):
        host = self.host
        if not host:
            message = 'Invalid host: {!r}'.format(host)
            raise ValueError(message)
        self.host_config = self.ssh_config.lookup(host)

    def setup_connect_parameters(self):
        """Fill connect parameters dict

        Get parameters values from below sources:
        - parameters passed to class constructor
        - parameters got from ~/.ssh/config and tobiko.conf
        - parameters got from fixture object attributes
        """

        # Get default parameter values from self object
        self.connect_parameters = parameters = items_from_object(
            schema=SSH_CONNECT_PARAMETERS, obj=self)
        LOG.debug('Default parameters for host %r:\n%r', self.host,
                  parameters)

        # Override parameters from host configuration files
        parameters.update(
            items_from_mapping(schema=SSH_CONNECT_PARAMETERS,
                               mapping=self.host_config.connect_parameters))
        LOG.debug('Configured connect parameters for host %r:\n%r',
                  self.host, parameters)

        # Override parameters with __init__ parameters
        parameters.update(
            items_from_mapping(schema=SSH_CONNECT_PARAMETERS,
                               mapping=self._connect_parameters))
        LOG.debug('Resulting connect parameters for host %r:\n%r', self.host,
                  parameters)

        # Validate hostname
        hostname = parameters.get('hostname')
        if not hostname:
            message = "Invalid hostname: {!r}".format(hostname)
            raise ValueError(message)

        # Expand key_filename
        key_filename = parameters.get('key_filename')
        if key_filename:
            key_filename = os.path.expanduser(key_filename)
            if not os.path.exists(key_filename):
                message = "key_filename {!r} doesn't exist".format(hostname)
                raise ValueError(message)
            parameters['key_filename'] = key_filename

        # Validate connection timeout
        timeout = parameters.get('timeout')
        if not timeout or timeout < 0.:
            message = "Invalid timeout: {!r}".format(timeout)
            raise ValueError(message)

        # Validate connection port
        port = parameters.get('port')
        if not port or port < 0 or port > 65535:
            message = "Invalid timeout: {!r}".format(port)
            raise ValueError(message)

    def setup_ssh_client(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()

        now = time.time()
        parameters = dict(self.connect_parameters)
        deadline = now + parameters.pop('timeout')
        sleep_time = self.connect_sleep_time
        login = self.connect_login
        while True:
            timeout = deadline - now
            LOG.debug("Logging in to %r... (time left %d seconds)", login,
                     timeout)
            try:
                sock = self._open_proxy_sock()
                client.connect(sock=sock, timeout=timeout, **parameters)
            except (EOFError, socket.error, socket.timeout,
                    paramiko.SSHException) as ex:
                now = time.time()
                if now + sleep_time >= deadline:
                    raise SSHConnectFailure(login=login, cause=ex)

                LOG.debug("Error logging in to  %s (%s); retrying in %d "
                          "seconds...", login, ex, sleep_time)
                time.sleep(sleep_time)
                sleep_time += self.connect_sleep_time_increment

            else:
                self.client = client
                self.addCleanup(client.close)
                LOG.info("Successfully logged it to %s", login)
                break

    def _open_proxy_sock(self):
        proxy_command = self.host_config.proxy_command or self.proxy_command
        proxy_client = self.proxy_client
        if proxy_client:
            # I need a command to execute with proxy client
            proxy_command = proxy_command or 'nc {hostname!r} {port!r}'
        elif not proxy_command:
            # Proxy sock is not required
            return None

        # Apply connect parameters to proxy command
        parameters = self.connect_parameters
        proxy_command = proxy_command.format(
            hostname=parameters['hostname'],
            port=parameters.get('port', 22))
        LOG.debug("Using proxy command: %r", proxy_command)

        if proxy_client:
            if isinstance(proxy_client, SSHClientFixture):
                # Connect to proxy server
                proxy_client = tobiko.setup_fixture(proxy_client).client

            # Open proxy channel
            LOG.debug("Execute proxy command with proxy client %r: %r",
                      proxy_client, proxy_command)
            proxy_sock = proxy_client.get_transport().open_session()
            proxy_sock.exec_command(proxy_command)
        else:
            LOG.debug("Execute proxy command on local host: %r", proxy_command)
            proxy_sock = paramiko.ProxyCommand(proxy_command)

        self.addCleanup(proxy_sock.close)
        return proxy_sock

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


def items_from_mapping(schema, mapping):
    return ((key, init(mapping.get(key)))
            for key, init in schema.items()
            if mapping.get(key) is not None)


def items_from_object(schema, obj):
    return {key: init(getattr(obj, key, None))
            for key, init in schema.items()
            if getattr(obj, key, None) is not None}


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
