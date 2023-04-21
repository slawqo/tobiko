# Copyright 2023 Red Hat
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

from collections import abc
import typing

import tobiko
from tobiko.openstack.neutron import _client


SubnetPoolType = typing.Dict[str, typing.Any]
SubnetPoolIdType = typing.Union[str, SubnetPoolType]


def get_subnet_pool_id(subnet_pool: SubnetPoolIdType) -> str:
    if isinstance(subnet_pool, str):
        return subnet_pool
    else:
        return subnet_pool['id']


def get_subnet_pool(subnet_pool: SubnetPoolIdType,
                    client: _client.NeutronClientType = None,
                    **params) -> SubnetPoolType:
    subnet_pool_id = get_subnet_pool_id(subnet_pool)
    try:
        return _client.neutron_client(client).show_subnetpool(
            subnet_pool_id, **params)['subnetpool']
    except _client.NotFound as ex:
        raise NoSuchSubnetPool from ex


def create_subnet_pool(client: _client.NeutronClientType = None,
                       add_cleanup: bool = True,
                       **params) -> SubnetPoolType:
    subnet_pool = _client.neutron_client(client).create_subnetpool(
        body={'subnetpool': params})['subnetpool']
    if add_cleanup:
        tobiko.add_cleanup(
            cleanup_subnet_pool, subnet_pool=subnet_pool, client=client)
    return subnet_pool


def cleanup_subnet_pool(subnet_pool: SubnetPoolIdType,
                        client: _client.NeutronClientType = None):
    try:
        delete_subnet_pool(subnet_pool=subnet_pool, client=client)
    except NoSuchSubnetPool:
        pass


def delete_subnet_pool(subnet_pool: SubnetPoolIdType,
                       client: _client.NeutronClientType = None):
    subnet_pool_id = get_subnet_pool_id(subnet_pool)
    try:
        _client.neutron_client(client).delete_subnetpool(subnet_pool_id)
    except _client.NotFound as ex:
        raise NoSuchSubnetPool from ex


def list_subnet_pools(client: _client.NeutronClientType = None,
                      **params) -> tobiko.Selection[SubnetPoolType]:
    subnet_pools = _client.neutron_client(client).list_subnetpools(**params)
    if isinstance(subnet_pools, abc.Mapping):
        subnet_pools = subnet_pools['subnetpools']
    return tobiko.select(subnet_pools)


def find_subnet_pool(client: _client.NeutronClientType = None,
                     unique=False,
                     **params) -> SubnetPoolType:
    """Look for a subnet pool matching some values"""
    subnet_pools = list_subnet_pools(client=client, **params)
    if subnet_pools:
        if unique:
            return subnet_pools.unique
        else:
            return subnet_pools.first
    else:
        raise NoSuchSubnetPool


class NoSuchSubnetPool(tobiko.ObjectNotFound):
    message = "No such subnet pool found"
