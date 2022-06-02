# Copyright 2019 Red Hat
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

import netaddr

import tobiko
from tobiko.openstack.neutron import _client


NetworkType = typing.Dict[str, typing.Any]
NetworkIdType = typing.Union[str, NetworkType]


class NoSuchNetwork(tobiko.ObjectNotFound):
    message = "No such network found for {id!r}"


def get_network_id(network: NetworkIdType) -> str:
    if isinstance(network, str):
        return network
    else:
        return network['id']


def get_network(network: NetworkIdType,
                client: _client.NeutronClientType = None,
                **params) -> NetworkType:
    network_id = get_network_id(network)
    try:
        return _client.neutron_client(client).show_network(
            network_id, **params)['network']
    except _client.neutronclient.exceptions.NotFound as ex:
        raise NoSuchNetwork(id=network_id) from ex


def list_networks(client: _client.NeutronClientType = None,
                  **params) -> \
        tobiko.Selection[NetworkType]:
    networks = _client.neutron_client(client).list_networks(
        **params)['networks']
    return tobiko.select(networks)


def find_network(client: _client.NeutronClientType = None,
                 unique=False,
                 default: NetworkType = None,
                 **attributes) -> NetworkType:
    """Look for a network matching some property values"""
    networks = list_networks(client=client, **attributes)
    if default is None or networks:
        if unique:
            return networks.unique
        else:
            return networks.first
    else:
        return default


def create_network(client: _client.NeutronClientType = None,
                   add_cleanup=True,
                   **params) -> NetworkType:
    network = _client.neutron_client(client).create_network(
        body={'network': params})['network']
    if add_cleanup:
        tobiko.add_cleanup(cleanup_network, network=network, client=client)
    return network


def cleanup_network(network: NetworkIdType,
                    client: _client.NeutronClientType = None):
    try:
        delete_network(network=network, client=client)
    except NoSuchNetwork:
        pass


def delete_network(network: NetworkIdType,
                   client: _client.NeutronClientType = None):
    network_id = get_network_id(network)
    try:
        _client.neutron_client(client).delete_network(network=network_id)
    except _client.NotFound as ex:
        raise NoSuchNetwork(id=network_id) from ex


def list_network_nameservers(network_id: typing.Optional[str] = None,
                             ip_version: typing.Optional[int] = None) -> \
        tobiko.Selection[netaddr.IPAddress]:
    from tobiko.openstack.neutron import _subnet
    subnets = _subnet.list_subnets(network_id=network_id)
    nameservers = tobiko.Selection[netaddr.IPAddress](
        netaddr.IPAddress(nameserver)
        for subnets in subnets
        for nameserver in subnets['dns_nameservers'])
    if ip_version is not None:
        nameservers = nameservers.with_attributes(version=ip_version)
    return nameservers
