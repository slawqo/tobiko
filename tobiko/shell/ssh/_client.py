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

import collections

import getpass
import os
import socket
import time
import subprocess

import paramiko
from oslo_log import log
import six

import tobiko
from tobiko.shell.ssh import _config
from tobiko.shell.ssh import _command


LOG = log.getLogger(__name__)


def valid_hostname(value):
    hostname = str(value)
    if not hostname:
        message = "Invalid hostname: {!r}".format(hostname)
        raise ValueError(message)
    return hostname


def valid_port(value):
    port = int(value)
    if port <= 0 or port > 65535:
        message = "Invalid port number: {!r}".format(port)
        raise ValueError(message)
    return port


def valid_path(value):
    return os.path.abspath(os.path.expanduser(value))


def positive_float(value):
    value = float(value)
    if value <= 0.:
        message = "{!r} is not positive".format(value)
        raise ValueError(message)
    return value


def positive_int(value):
    value = int(value)
    if value <= 0:
        message = "{!r} is not positive".format(value)
        raise ValueError(message)
    return value


def key_filename(value):
    if isinstance(value, six.string_types):
        value = [value]
    return [os.path.realpath(os.path.expanduser(v)) for v in value]


SSH_CONNECT_PARAMETERS = {
    #: The server to connect to
    'hostname': valid_hostname,

    #: The server port to connect to
    'port': valid_port,

    #: The username to authenticate as (defaults to the current local username)
    'username': str,

    #: Used for password authentication; is also used for private key
    #: decryption if passphrase is not given
    'password': str,

    #: Used for decrypting private keys
    'passphrase': str,

    #: The filename, or list of filenames, of optional private key(s) and/or
    #: certs to try for authentication
    'key_filename': key_filename,

    #: An optional timeout (in seconds) for the TCP connect
    'timeout': positive_float,

    #: Set to False to disable connecting to the SSH agent
    'allow_agent': bool,

    #: Set to False to disable searching for discoverable private key files in
    #: ~/.ssh/
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
    #: name of the host being connected to (default True).
    'gss_trust_dns': bool,

    #: An optional timeout (in seconds) to wait for the SSH banner to be
    #: presented.
    'banner_timeout': positive_float,

    #: An optional timeout (in seconds) to wait for an authentication response
    'auth_timeout': positive_float,

    #: Number of connection attempts to be tried before timeout
    'connection_attempts': positive_int,

    #: Minimum amount of time to wait between two connection attempts
    'connection_interval': positive_float,

    #: Command to be executed to open proxy sock
    'proxy_command': str,
}


def gather_ssh_connect_parameters(source=None, destination=None, schema=None,
                                  remove_from_schema=False, **kwargs):
    if schema is None:
        assert not remove_from_schema
        schema = SSH_CONNECT_PARAMETERS
    parameters = {}

    if source:
        # gather from object
        if isinstance(source, collections.Mapping):
            parameters.update(_items_from_mapping(mapping=source,
                                                  schema=schema))
        else:
            parameters.update(_items_from_object(obj=source,
                                                 schema=schema))

    if kwargs:
        # gather from kwargs
        parameters.update(_items_from_mapping(mapping=kwargs, schema=schema))
        kwargs = exclude_mapping_items(kwargs, schema)
        if kwargs:
            message = "Invalid SSH connection parameters: {!r}".format(kwargs)
            raise ValueError(message)

    if remove_from_schema and parameters:
        # update schema
        for name in parameters:
            del schema[name]

    if destination is not None:
        destination.update(parameters)
    return parameters


def _items_from_mapping(mapping, schema):
    for name, init in schema.items():
        value = mapping.get(name)
        if value is not None:
            yield name, init(value)


def _items_from_object(obj, schema):
    for name, init in schema.items():
        value = getattr(obj, name, None)
        if value is not None:
            yield name, init(value)


def exclude_mapping_items(mapping, exclude):
        # Exclude parameters that are already in target dictionary
    return {key: value
            for key, value in mapping.items()
            if key not in exclude}


class SSHConnectFailure(tobiko.TobikoException):
    message = "Failed to login to {login}\n{cause}"


class SSHClientFixture(tobiko.SharedFixture):

    host = None
    port = 22
    username = getpass.getuser()

    client = None

    default = tobiko.required_setup_fixture(_config.SSHDefaultConfigFixture)
    config_files = None
    host_config = None

    proxy_client = None
    proxy_sock = None
    connect_parameters = None
    schema = SSH_CONNECT_PARAMETERS

    def __init__(self, host=None, proxy_client=None, host_config=None,
                 config_files=None, schema=None, **kwargs):
        super(SSHClientFixture, self).__init__()
        if host:
            self.host = host
        if proxy_client:
            self.proxy_client = proxy_client
        if host_config:
            self.host_config = host_config
        if config_files:
            self.config_files = config_files

        self.schema = schema = dict(schema or self.schema)
        self._connect_parameters = gather_ssh_connect_parameters(
            schema=schema, **kwargs)
        self._forwarders = []

    def setup_fixture(self):
        self.setup_connect_parameters()
        self.setup_ssh_client()

    def setup_host_config(self):
        if not self.host_config:
            self.host_config = _config.ssh_host_config(
                host=self.host, config_files=self.config_files)
        return self.host_config

    def setup_connect_parameters(self):
        """Fill connect parameters dict

        Get parameters values from below sources:
        - parameters passed to class constructor
        - parameters got from ~/.ssh/config and tobiko.conf
        - parameters got from fixture object attributes
        """
        self.setup_host_config()
        if not self.connect_parameters:
            self.connect_parameters = self.get_connect_parameters()
        return self.connect_parameters

    def get_connect_parameters(self, schema=None):
        schema = dict(schema or self.schema)
        parameters = {}
        for gather_parameters in [self.gather_initial_connect_parameters,
                                  self.gather_host_config_connect_parameters,
                                  self.gather_default_connect_parameters]:
            gather_parameters(destination=parameters,
                              schema=schema,
                              remove_from_schema=True)
        if parameters:
            LOG.debug('SSH connect parameters for host %r:\n%r', self.host,
                      parameters)
        return parameters

    def gather_initial_connect_parameters(self, **kwargs):
        parameters = gather_ssh_connect_parameters(
            source=self._connect_parameters, **kwargs)
        if parameters:
            LOG.debug('Initial SSH connect parameters for host %r:\n'
                      '%r', self.host, parameters)
        return parameters

    def gather_host_config_connect_parameters(self, **kwargs):
        parameters = gather_ssh_connect_parameters(
            source=self.host_config.connect_parameters, **kwargs)
        if parameters:
            LOG.debug('Host configured SSH connect parameters for host %r:\n'
                      '%r', self.host, parameters)
        return parameters

    def gather_default_connect_parameters(self, **kwargs):
        parameters = gather_ssh_connect_parameters(source=self, **kwargs)
        if parameters:
            LOG.debug('Default SSH connect parameters for host %r:\n'
                      '%r', self.host, parameters)
        return parameters

    def setup_ssh_client(self):
        self.client, self.proxy_sock = ssh_connect(
            proxy_client=self.proxy_client,
            **self.connect_parameters)
        self.addCleanup(self.cleanup_ssh_client)
        if self.proxy_sock:
            self.addCleanup(self.cleanup_proxy_sock)
        for forwarder in self._forwarders:
            self.useFixture(forwarder)

    def cleanup_ssh_client(self):
        client = self.client
        self.client = None
        if client:
            try:
                client.close()
            except Exception:
                LOG.exception('Error closing client (%r)', self)

    def cleanup_proxy_sock(self):
        proxy_sock = self.proxy_sock
        self.proxy_sock = None
        if proxy_sock:
            try:
                proxy_sock.close()
            except Exception:
                LOG.exception('Error closing proxy socket (%r)', self)

    def connect(self):
        return tobiko.setup_fixture(self).client


UNDEFINED_CLIENT = 'UNDEFINED_CLIENT'


class SSHClientManager(object):

    default = tobiko.required_setup_fixture(_config.SSHDefaultConfigFixture)

    def __init__(self):
        self.clients = {}

    def get_client(self, host, username=None, port=None, proxy_jump=None,
                   host_config=None, config_files=None, proxy_client=None,
                   **connect_parameters):
        host_config = host_config or _config.ssh_host_config(
            host=host, config_files=config_files)
        hostname = host_config.hostname
        port = port or host_config.port
        username = username or host_config.username
        host_key = hostname, port, username, proxy_jump
        client = self.clients.get(host_key, UNDEFINED_CLIENT)
        if client is UNDEFINED_CLIENT:
            # Put a placeholder client to avoid infinite recursive lookup
            self.clients[host_key] = None
            proxy_client = proxy_client or self.get_proxy_client(
                host=host, proxy_jump=proxy_jump, config_files=config_files)
            self.clients[host_key] = client = SSHClientFixture(
                host=host, hostname=hostname, port=port, username=username,
                proxy_client=proxy_client, host_config=host_config,
                **connect_parameters)
        return client

    def get_proxy_client(self, host=None, proxy_jump=None, host_config=None,
                         config_files=None):
        if isinstance(proxy_jump, SSHClientFixture):
            return proxy_jump
        host_config = host_config or _config.ssh_host_config(
            host=host, config_files=config_files)
        proxy_host = host_config.proxy_jump
        return proxy_host and self.get_client(proxy_host) or None


CLIENTS = SSHClientManager()


def ssh_client(host, port=None, username=None, proxy_jump=None,
               host_config=None, config_files=None, manager=None,
               **connect_parameters):
    manager = manager or CLIENTS
    return manager.get_client(host=host, port=port, username=username,
                              proxy_jump=proxy_jump, host_config=host_config,
                              config_files=config_files,
                              **connect_parameters)


def ssh_connect(hostname, username=None, port=None, connection_interval=None,
                connection_attempts=None, proxy_command=None,
                proxy_client=None, **parameters):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    login = _command.ssh_login(hostname=hostname, username=username, port=port)
    attempts = connection_attempts or 1
    interval = connection_interval or 5.
    for attempt in range(1, attempts + 1):
        LOG.debug("Logging in to %r (%r)... attempt %d out of %d",
                  login, parameters, attempt, attempts)
        start_time = time.time()
        proxy_sock = ssh_proxy_sock(hostname=hostname,
                                    port=port,
                                    command=proxy_command,
                                    client=proxy_client)
        try:
            client.connect(hostname=hostname,
                           username=username,
                           port=port,
                           sock=proxy_sock,
                           **parameters)
        except (EOFError, socket.error, socket.timeout,
                paramiko.SSHException) as ex:
            if attempt >= attempts:
                raise

            LOG.debug("Error logging in to %r: \n(%s)", login, ex,
                      exc_info=1)
            sleep_time = start_time + interval - time.time()
            if sleep_time > 0.:
                LOG.debug("Retrying connecting to %r in %d seconds...", login,
                          sleep_time)
                time.sleep(sleep_time)

        else:
            LOG.info("Successfully logged it to %s", login)
            return client, proxy_sock


def ssh_proxy_sock(hostname, port=None, command=None, client=None,
                   source_address=None):
    if not command:
        if client:
            # I need a command to execute with proxy client
            options = []
            if source_address:
                options += ['-s', str(source_address)]
            command = ['nc'] + options + ['{hostname!s}', '{port!s}']
        elif not command:
            # Proxy sock is not required
            return None

    # Apply connect parameters to proxy command
    if not isinstance(command, six.string_types):
        command = subprocess.list2cmdline(command)
    command = command.format(hostname=hostname, port=(port or 22))
    if client:
        if isinstance(client, SSHClientFixture):
            # Connect to proxy server
            client = client.connect()
        elif not isinstance(client, paramiko.SSHClient):
            message = "Object {!r} is not an SSHClient".format(client)
            raise TypeError(message)

        # Open proxy channel
        LOG.debug("Execute proxy command with proxy client %r: %r",
                  client, command)
        sock = client.get_transport().open_session()
        sock.exec_command(command)
    else:
        LOG.debug("Execute proxy command on local host: %r", command)
        sock = paramiko.ProxyCommand(command)

    return sock


def ssh_proxy_client(manager=None, host=None, host_config=None,
                     config_files=None):
    manager = manager or CLIENTS
    return manager.get_proxy_client(host=host,
                                    host_config=host_config,
                                    config_files=config_files)
