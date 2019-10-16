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

import collections

import netaddr
from neutronclient.v2_0 import client as neutronclient

import tobiko
from tobiko.openstack import _client


class NeutronClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        return neutronclient.Client(session=session)


class NeutronClientManager(_client.OpenstackClientManager):

    def create_client(self, session):
        return NeutronClientFixture(session=session)


CLIENTS = NeutronClientManager()


def neutron_client(obj):
    if not obj:
        return get_neutron_client()

    if isinstance(obj, neutronclient.Client):
        return obj

    fixture = tobiko.setup_fixture(obj)
    if isinstance(fixture, NeutronClientFixture):
        return fixture.client

    message = "Object {!r} is not a NeutronClientFixture".format(obj)
    raise TypeError(message)


def get_neutron_client(session=None, shared=True, init_client=None,
                       manager=None):
    manager = manager or CLIENTS
    client = manager.get_client(session=session, shared=shared,
                                init_client=init_client)
    tobiko.setup_fixture(client)
    return client.client


_RAISE_ERROR = object()


def find_network(client=None, unique=False, default=_RAISE_ERROR,
                 **attributes):
    """Look for a network matching some property values"""
    networks = list_networks(client=client, **attributes)
    if default is _RAISE_ERROR or networks:
        if unique:
            return networks.unique
        else:
            return networks.first
    else:
        return default


def find_port(client=None, unique=False, default=_RAISE_ERROR, **attributes):
    """Look for a port matching some property values"""
    ports = list_ports(client=client, **attributes)
    if default is _RAISE_ERROR or ports:
        if unique:
            return ports.unique
        else:
            return ports.first
    else:
        return default


def find_subnet(client=None, unique=False, default=_RAISE_ERROR, **attributes):
    """Look for a subnet matching some property values"""
    subnets = list_subnets(client=client, **attributes)
    if default is _RAISE_ERROR or subnets:
        if unique:
            return subnets.unique
        else:
            return subnets.first
    else:
        return default


def list_networks(client=None, **params):
    networks = neutron_client(client).list_networks(**params)['networks']
    return tobiko.select(networks)


def list_ports(client=None, **params):
    ports = neutron_client(client).list_ports(**params)['ports']
    return tobiko.select(ports)


def list_subnets(client=None, **params):
    subnets = neutron_client(client).list_subnets(**params)
    if isinstance(subnets, collections.Mapping):
        subnets = subnets['subnets']
    return tobiko.select(subnets)


def list_agents(client=None, **params):
    agents = neutron_client(client).list_agents(**params)
    if isinstance(agents, collections.Mapping):
        agents = agents['agents']
    return tobiko.select(agents)


def list_subnet_cidrs(client=None, **params):
    return tobiko.select(netaddr.IPNetwork(subnet['cidr'])
                         for subnet in list_subnets(client=client, **params))


def get_network(network, client=None, **params):
    return neutron_client(client).show_network(network, **params)['network']


def get_port(port, client=None, **params):
    return neutron_client(client).show_port(port, **params)['port']


def get_router(router, client=None, **params):
    return neutron_client(client).show_router(router, **params)['router']


def get_subnet(subnet, client=None, **params):
    return neutron_client(client).show_subnet(subnet, **params)['subnet']


def list_l3_agent_hosting_routers(router, client=None, **params):
    agents = neutron_client(client).list_l3_agent_hosting_routers(
        router, **params)
    if isinstance(agents, collections.Mapping):
        agents = agents['agents']
    return tobiko.select(agents)


def find_l3_agent_hosting_router(router, client=None, unique=False,
                                 default=_RAISE_ERROR, **params):
    agents = list_l3_agent_hosting_routers(router=router, client=client,
                                           **params)
    if default is _RAISE_ERROR or agents:
        if unique:
            return agents.unique
        else:
            return agents.first
    else:
        return default
