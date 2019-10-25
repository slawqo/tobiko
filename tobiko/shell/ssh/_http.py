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
import functools

import requests
from urllib3 import connection
from urllib3 import connectionpool
from urllib3 import poolmanager

import tobiko
from tobiko.shell.ssh import _client
from tobiko.shell.ssh import _forward


def setup_http_session_ssh_tunneling(session=None, ssh_client=None):
    session = session or requests.Session()
    ssh_client = ssh_client or _client.ssh_proxy_client()
    if ssh_client is not None:
        for adapter in session.adapters.values():
            manager = adapter.poolmanager
            manager.pool_classes_by_scheme = pool_classes_by_scheme.copy()
            manager.key_fn_by_scheme = key_fn_by_scheme.copy()
            manager.connection_pool_kw['ssh_client'] = ssh_client
    return session


# pylint: disable=protected-access

# All known keyword arguments that could be provided to the pool manager, its
# pools, or the underlying connections. This is used to construct a pool key.
_key_fields = poolmanager._key_fields + ('key_ssh_client',)


class SSHTunnelPoolKey(
        collections.namedtuple("SSHTunnelPoolKey", _key_fields)):
    """The namedtuple class used to construct keys for the connection pool.

    All custom key schemes should include the fields in this key at a minimum.
    """


#: A dictionary that maps a scheme to a callable that creates a pool key.
#: This can be used to alter the way pool keys are constructed, if desired.
#: Each PoolManager makes a copy of this dictionary so they can be configured
#: globally here, or individually on the instance.
key_fn_by_scheme = {
    "http": functools.partial(poolmanager._default_key_normalizer,
                              SSHTunnelPoolKey),
    "https": functools.partial(poolmanager._default_key_normalizer,
                               SSHTunnelPoolKey),
}

# pylint: enable=protected-access


class SSHTunnelHTTPConnection(connection.HTTPConnection):

    def __init__(self, local_address, *args, **kwargs):
        super(SSHTunnelHTTPConnection, self).__init__(*args, **kwargs)
        self.local_address = local_address

    def _new_conn(self):
        """ Establish a socket connection and set nodelay settings on it.

        :return: New socket connection.
        """
        extra_kw = {}
        if self.source_address:
            extra_kw["source_address"] = self.source_address

        if self.socket_options:
            extra_kw["socket_options"] = self.socket_options

        try:
            conn = connection.connection.create_connection(
                self.local_address, self.timeout, **extra_kw)

        except connection.SocketTimeout:
            raise connection.ConnectTimeoutError(
                self,
                "Connection to %s timed out. (connect timeout=%s)"
                % (self.host, self.timeout),
            )

        except connection.SocketError as e:
            raise connection.NewConnectionError(
                self, "Failed to establish a new connection: %s" % e
            )

        return conn


class SSHTunnelHTTPSConnection(SSHTunnelHTTPConnection,
                               connection.HTTPSConnection):
    pass


class SSHTunnelHTTPConnectionPool(connectionpool.HTTPConnectionPool):

    ConnectionCls = SSHTunnelHTTPConnection

    def __init__(self, host, port, ssh_client, **kwargs):
        self.forwarder = forwarder = _forward.SSHTunnelForwarderFixture(
            ssh_client=ssh_client)
        local_address = forwarder.put_forwarding(host, port)
        tobiko.setup_fixture(forwarder)
        super(SSHTunnelHTTPConnectionPool, self).__init__(
            host=host, port=port, local_address=local_address, **kwargs)


class SSHTunnelHTTPSConnectionPool(SSHTunnelHTTPConnectionPool,
                                   connectionpool.HTTPSConnectionPool):

    ConnectionCls = SSHTunnelHTTPSConnection


pool_classes_by_scheme = {"http": SSHTunnelHTTPConnectionPool,
                          "https": SSHTunnelHTTPSConnectionPool}
