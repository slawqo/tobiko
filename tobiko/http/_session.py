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
from urllib3 import poolmanager

from tobiko.http import _connection


def get_http_session(ssh_client=None):
    return setup_http_session(session=requests.Session(),
                              ssh_client=ssh_client)


def setup_http_session(session, ssh_client=None):
    for adapter in session.adapters.values():
        manager = adapter.poolmanager
        manager.pool_classes_by_scheme = pool_classes_by_scheme.copy()
        manager.key_fn_by_scheme = key_fn_by_scheme.copy()
        manager.connection_pool_kw['ssh_client'] = ssh_client
    return session


# pylint: disable=protected-access

# All known keyword arguments that could be provided to the pool manager, its
# pools, or the underlying connections. This is used to construct a pool key.
_key_fields = tuple(poolmanager._key_fields) + ('key_ssh_client',)


class PoolKey(collections.namedtuple("PoolKey", _key_fields)):  # type: ignore
    """The namedtuple class used to construct keys for the connection pool.

    All custom key schemes should include the fields in this key at a minimum.
    """


#: A dictionary that maps a scheme to a callable that creates a pool key.
#: This can be used to alter the way pool keys are constructed, if desired.
#: Each PoolManager makes a copy of this dictionary so they can be configured
#: globally here, or individually on the instance.
key_fn_by_scheme = {
    "http": functools.partial(poolmanager._default_key_normalizer,
                              PoolKey),
    "https": functools.partial(poolmanager._default_key_normalizer,
                               PoolKey),
}

# pylint: enable=protected-access


pool_classes_by_scheme = {"http": _connection.HTTPConnectionPool,
                          "https": _connection.HTTPSConnectionPool}
