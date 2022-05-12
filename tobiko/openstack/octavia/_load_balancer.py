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

import typing

from tobiko.openstack.octavia import _client

LoadBalancerType = typing.Dict[str, typing.Any]
LoadBalancerIdType = typing.Union[str, LoadBalancerType]


def get_load_balancer_id(load_balancer: LoadBalancerIdType) -> str:
    if isinstance(load_balancer, str):
        return load_balancer
    else:
        return load_balancer['id']


def get_load_balancer(load_balancer: LoadBalancerIdType,
                      client: _client.OctaviaClientType = None) \
        -> LoadBalancerType:
    load_balancer_id = get_load_balancer_id(load_balancer)
    return _client.octavia_client(client).load_balancer_show(
        load_balancer_id)
