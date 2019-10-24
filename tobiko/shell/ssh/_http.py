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

from tobiko.shell.ssh import _client


def ssh_tunnel_http_session(ssh_client=None):
    ssh_client = ssh_client or _client.ssh_proxy_client()
    if ssh_client is None:
        return None

    session = requests.Session()
    mount_ssh_tunnel_http_adapter(session=session, ssh_client=ssh_client)
    return session


def mount_ssh_tunnel_http_adapter(session, ssh_client):
    adapter = SSHTunnelHttpAdapter(ssh_client=ssh_client)
    for scheme in list(session.adapters):
        session.mount(scheme, adapter)


class SSHTunnelHttpAdapter(requests.adapters.HTTPAdapter):
    """The custom adapter used to set tunnel HTTP connections over SSH tunnel

    """

    def __init__(self, ssh_client, *args, **kwargs):
        self.ssh_client = ssh_client
        super(SSHTunnelHttpAdapter, self).__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize,
                         block=requests.adapters.DEFAULT_POOLBLOCK,
                         **pool_kwargs):
        # save these values for pickling
        self._pool_connections = connections
        self._pool_maxsize = maxsize
        self._pool_block = block
        self.poolmanager = SSHTunnelPoolManager(
            num_pools=connections, maxsize=maxsize, block=block, strict=True,
            ssh_client=self.ssh_client, **pool_kwargs)


class SSHTunnelPoolManager(poolmanager.PoolManager):

    def __init__(self, *args, **kwargs):
        super(SSHTunnelPoolManager, self).__init__(*args, **kwargs)
        # Locally set the pool classes and keys so other PoolManagers can
        # override them.
        self.pool_classes_by_scheme = pool_classes_by_scheme
        self.key_fn_by_scheme = key_fn_by_scheme.copy()


# pylint: disable=protected-access

# All known keyword arguments that could be provided to the pool manager, its
# pools, or the underlying connections. This is used to construct a pool key.
_key_fields = poolmanager._key_fields + ('key_ssh_client',)

#: The namedtuple class used to construct keys for the connection pool.
#: All custom key schemes should include the fields in this key at a minimum.
SSHTunnelPoolKey = collections.namedtuple("SSHTunnelPoolKey", _key_fields)

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

    def __init__(self, *args, **kw):
        self.ssh_client = kw.pop('ssh_client')
        assert self.ssh_client is not None
        super(SSHTunnelHTTPConnection, self).__init__(*args, **kw)

    def _new_conn(self):
        """ Establish a socket connection and set nodelay settings on it.

        :return: New socket connection.
        """
        return _client.ssh_proxy_sock(hostname=self._dns_host,
                                      port=self.port,
                                      source_address=self.source_address,
                                      client=self.ssh_client)


class SSHTunnelHTTPSConnection(SSHTunnelHTTPConnection,
                               connection.HTTPSConnection):
    pass


class SSHTunnelHTTPConnectionPool(connectionpool.HTTPConnectionPool):

    ConnectionCls = SSHTunnelHTTPConnection


class SSHTunnelHTTPSConnectionPool(connectionpool.HTTPSConnectionPool):

    ConnectionCls = SSHTunnelHTTPSConnection


pool_classes_by_scheme = {"http": SSHTunnelHTTPConnectionPool,
                          "https": SSHTunnelHTTPSConnectionPool}
