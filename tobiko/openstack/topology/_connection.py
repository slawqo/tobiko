# Copyright 2020 Red Hat
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
import typing

import netaddr
from oslo_log import log

import tobiko
from tobiko.openstack.topology import _config
from tobiko.shell import ssh

LOG = log.getLogger(__name__)


class UreachableSSHServer(tobiko.TobikoException):
    message = ("Unable to reach SSH server through any address: {addresses}. "
               "Failures: {failures}")


class SSHConnection(object):

    def __init__(self,
                 address: netaddr.IPAddress,
                 ssh_client: typing.Optional[ssh.SSHClientFixture] = None,
                 proxy_client: typing.Optional[ssh.SSHClientFixture] = None,
                 failure: typing.Optional[Exception] = None):
        self.address = address
        self.ssh_client = ssh_client
        self.proxy_client = proxy_client
        self.failure = failure

    def __repr__(self) -> str:
        attributes = ", ".join(f"{n}={v!r}"
                               for n, v in self._iter_attributes())
        return f"{type(self).__name__}({attributes})"

    def _iter_attributes(self):
        yield 'address', self.address
        if self.ssh_client is not None:
            yield 'ssh_client', self.ssh_client
        if self.proxy_client is not None:
            yield 'proxy_client', self.proxy_client
        if self.failure is not None:
            yield 'failure', self.failure

    @property
    def is_valid(self) -> bool:
        return (self.failure is None and
                self.ssh_client is not None)


SSHConnectionKey = typing.Tuple[netaddr.IPAddress,
                                typing.Optional[ssh.SSHClientFixture]]
SSHConnectionDict = typing.Dict[SSHConnectionKey, SSHConnection]


class SSHConnectionManager(tobiko.SharedFixture):

    config = tobiko.required_setup_fixture(_config.OpenStackTopologyConfig)

    def __init__(self):
        super(SSHConnectionManager, self).__init__()
        self._connections: SSHConnectionDict = collections.OrderedDict()

    def cleanup_fixture(self):
        connections = list(self._connections.values())
        self._connections.clear()
        for connection in connections:
            ssh_client = connection.ssh_client
            if ssh_client is not None:
                ssh_client.close()

    def connect(self,
                addresses: typing.List[netaddr.IPAddress],
                proxy_client: typing.Optional[ssh.SSHClientFixture] = None,
                **connect_parameters) \
            -> ssh.SSHClientFixture:
        if not addresses:
            raise ValueError(f"'addresses' list is empty: {addresses}")
        connections = self.list_connections(addresses,
                                            proxy_client=proxy_client)
        try:
            connection = connections.with_attributes(is_valid=True).first
        except tobiko.ObjectNotFound:
            pass
        else:
            assert isinstance(connection.ssh_client, ssh.SSHClientFixture)
            return connection.ssh_client

        for connection in connections.with_attributes(failure=None):
            # connection not tried yet
            LOG.debug("Establishing SSH connection to "
                      f"'{connection.address}' (proxy_client={proxy_client})")
            try:
                ssh_client = self.ssh_client(connection.address,
                                             proxy_client=proxy_client,
                                             **connect_parameters)
                ssh_client.connect(retry_count=1, connection_attempts=1)
            except Exception as ex:
                LOG.debug("Failed establishing SSH connect to "
                          f"'{connection.address}': {ex}")
                # avoid re-checking again later the same address
                connection.failure = ex
                continue
            else:
                # cache valid connection SSH client for later use
                connection.ssh_client = ssh_client
                assert connection.is_valid
                return ssh_client

        failures = '\n'.join(str(connection.failure)
                             for connection in connections)
        raise UreachableSSHServer(addresses=addresses,
                                  failures=failures)

    def list_connections(
            self,
            addresses: typing.List[netaddr.IPAddress],
            proxy_client: ssh.SSHClientFixture = None) \
            -> tobiko.Selection[SSHConnection]:
        # Ensure there is any address duplication
        addresses = list(collections.OrderedDict.fromkeys(addresses))
        return tobiko.Selection[SSHConnection](
            self.get_connection(address, proxy_client=proxy_client)
            for address in addresses)

    def get_connection(
            self,
            address: netaddr.IPAddress,
            proxy_client: ssh.SSHClientFixture = None) \
            -> SSHConnection:
        tobiko.check_valid_type(address, netaddr.IPAddress)
        tobiko.check_valid_type(proxy_client, ssh.SSHClientFixture,
                                type(None))
        connection = SSHConnection(address, proxy_client=proxy_client)
        return self._connections.setdefault((address, proxy_client),
                                            connection)

    def ssh_client(self, address, username=None, port=None,
                   key_filename=None, **ssh_parameters):
        username = username or self.config.conf.username
        port = port or self.config.conf.port
        key_filename = key_filename or self.config.conf.key_file
        return ssh.ssh_client(host=str(address),
                              username=username,
                              key_filename=key_filename,
                              **ssh_parameters)


SSH_CONNECTIONS = SSHConnectionManager()


def ssh_connect(addresses: typing.List[netaddr.IPAddress],
                manager: typing.Optional[SSHConnectionManager] = None,
                **connect_parameters) -> ssh.SSHClientFixture:
    manager = manager or SSH_CONNECTIONS
    return manager.connect(addresses=addresses, **connect_parameters)
