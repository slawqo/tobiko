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


class NoSuchNetwork(tobiko.ObjectNotFound):
    message = "No such network found for {id!r}"


NeutronNetworkType = typing.Dict[str, typing.Any]


def get_network(network, client=None, **params) -> NeutronNetworkType:
    try:
        return _client.neutron_client(
            client).show_network(network, **params)['network']
    except _client.neutronclient.exceptions.NotFound as ex:
        raise NoSuchNetwork(id=network) from ex


def list_networks(client=None, **params) -> \
        tobiko.Selection[NeutronNetworkType]:
    networks = _client.neutron_client(client).list_networks(
        **params)['networks']
    return tobiko.select(networks)


_RAISE_ERROR = object()


def find_network(client=None, unique=False, default=_RAISE_ERROR,
                 **attributes) -> NeutronNetworkType:
    """Look for a network matching some property values"""
    networks = list_networks(client=client, **attributes)
    if default is _RAISE_ERROR or networks:
        if unique:
            return networks.unique
        else:
            return networks.first
    else:
        return default


def create_network(client=None, **params) -> NeutronNetworkType:
    return _client.neutron_client(client).create_network(
        body={'network': params})['network']


def delete_network(network, client=None):
    return _client.neutron_client(client).delete_network(network=network)


class NeutronNetworkFixture(_client.HasNeutronClientFixture):

    details: typing.Optional[NeutronNetworkType] = None

    def __init__(self, name: typing.Optional[str] = None,
                 obj: _client.NeutronClientType = None):
        super(NeutronNetworkFixture, self).__init__(obj=obj)
        if name is None:
            name = self.fixture_name
        self.name: str = name

    @property
    def id(self):
        return self.details['id']

    def setup_fixture(self):
        super(NeutronNetworkFixture, self).setup_fixture()
        self.name = self.fixture_name
        self.details = create_network(client=self.client, name=self.name)
        self.addCleanup(delete_network, network=self.id, client=self.client)


def list_network_nameservers(network_id: typing.Optional[str] = None,
                             ip_version: typing.Optional[int] = None) -> \
        tobiko.Selection[netaddr.IPAddress]:
    subnets = _client.list_subnets(network_id=network_id)
    nameservers = tobiko.Selection[netaddr.IPAddress](
        netaddr.IPAddress(nameserver)
        for subnets in subnets
        for nameserver in subnets['dns_nameservers'])
    if ip_version is not None:
        nameservers = nameservers.with_attributes(version=ip_version)
    return nameservers
