# Copyright 2022 Red Hat
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

import tobiko
from tobiko.openstack import nova
from tobiko.shiftstack import _keystone


def shiftstack_nova_client(obj: nova.NovaClientType) -> nova.NovaClient:
    if obj is None:
        return get_shiftstack_nova_client()
    else:
        return tobiko.check_valid_type(obj, nova.NovaClient)


def get_shiftstack_nova_client() -> nova.NovaClient:
    session = _keystone.shiftstack_keystone_session()
    return nova.get_nova_client(session=session)


def list_shiftstack_nodes(client: nova.NovaClientType = None,
                          **params):
    client = shiftstack_nova_client(client)
    return nova.list_servers(client=client, **params)


def find_shiftstack_node(client: nova.NovaClientType = None,
                         **params):
    client = shiftstack_nova_client(client)
    return nova.find_server(client=client, **params)
