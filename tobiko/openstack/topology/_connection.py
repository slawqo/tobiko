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
                 failure: typing.Optional[Exception] = None):
        self.address = address
        self.ssh_client = ssh_client
        self.failure = failure

    def __repr__(self) -> str:
        attributes = ", ".join(f"{n}={v!r}"
                               for n, v in self._iter_attributes())
        return f"{type(self).__name__}({attributes})"

    def _iter_attributes(self):
        yield 'address', self.address
        if self.ssh_client is not None:
            yield 'ssh_client', self.ssh_client
        if self.failure is not None:
            yield 'failure', self.failure

    @property
    def is_valid(self) -> bool:
        return (self.failure is None and
                self.ssh_client is not None)


class SSHConnectionManager(tobiko.SharedFixture):

    config = tobiko.required_setup_fixture(_config.OpenStackTopologyConfig)

    def __init__(self):
        super(SSHConnectionManager, self).__init__()
        self._connections: typing.Dict[netaddr.IPAddress, SSHConnection] = (
            collections.OrderedDict())

    def cleanup_fixture(self):
        connections = list(self._connections.values())
        self._connections.clear()
        for connection in connections:
            connection.close()

    def connect(self,
                addresses: typing.List[netaddr.IPAddress],
                **connect_parameters) -> ssh.SSHClientFixture:
        if not addresses:
            raise ValueError(f"'addresses' list is empty: {addresses}")

        connections = tobiko.select(self.list_connections(addresses))
        try:
            return connections.with_attributes(is_valid=True).first.ssh_client
        except tobiko.ObjectNotFound:
            pass

        for connection in connections.with_attributes(failure=None):
            # connection not tried yet
            LOG.debug("Establishing SSH connection to "
                      f"'{connection.address}'")
            try:
                ssh_client = self.ssh_client(connection.address,
                                             **connect_parameters)
                ssh_client.connect(retry_count=1, connection_attempts=1)
            except Exception as ex:
                LOG.debug("Failed establishing SSH connect to "
                          f"'{connection.address}'.", exc_info=1)
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

    def list_connections(self, addresses: typing.List[netaddr.IPAddress]) -> \
            typing.List[SSHConnection]:
        connections = []
        for address in addresses:
            connections.append(self.get_connection(address))
        return connections

    def get_connection(self, address: netaddr.IPAddress):
        tobiko.check_valid_type(address, netaddr.IPAddress)
        return self._connections.setdefault(address,
                                            SSHConnection(address))

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
