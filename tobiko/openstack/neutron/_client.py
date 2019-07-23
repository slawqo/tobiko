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
from tobiko.openstack import _find


class NeutronClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        return neutronclient.Client(session=session)


class NeutronClientManatger(_client.OpenstackClientManager):

    def create_client(self, session):
        return NeutronClientFixture(session=session)


CLIENTS = NeutronClientManatger()


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


def find_network(obj, properties=None, client=None, check_found=True,
                 check_unique=True, **params):
    """Look for a network matching some property values"""
    resources = list_networks(client=client, **params)
    return _find.find_resource(obj=obj,
                               resources=resources,
                               properties=properties,
                               check_found=check_found,
                               check_unique=check_unique)


def find_port(obj, properties=None, client=None, check_found=True,
              check_unique=True, **params):
    """Look for a port matching some property values"""
    resources = list_ports(client=client, **params)
    return _find.find_resource(obj=obj,
                               resources=resources,
                               properties=properties,
                               check_found=check_found,
                               check_unique=check_unique)


def find_subnet(obj, properties=None, client=None, check_found=True,
                check_unique=False, **params):
    """Look for a subnet matching some property values"""
    resources = list_subnets(client=client, **params)
    return _find.find_resource(obj=obj,
                               resources=resources,
                               properties=properties,
                               check_found=check_found,
                               check_unique=check_unique)


def list_networks(show=False, client=None, **params):
    networks = neutron_client(client).list_networks(**params)['networks']
    if show:
        networks = [show_network(n['id'], client=client) for n in networks]
    return networks


def list_ports(show=False, client=None, **params):
    ports = neutron_client(client).list_ports(**params)['ports']
    if show:
        ports = [show_port(p['id'], client=client) for p in ports]
    return ports


def list_subnets(show=False, client=None, **params):
    subnets = neutron_client(client).list_subnets(**params)
    if isinstance(subnets, collections.Mapping):
        subnets = subnets['subnets']
    if show:
        subnets = [show_subnet(s['id'], client=client) for s in subnets]
    return subnets


def list_agents(client=None, **params):
    agents = neutron_client(client).list_agents(**params)
    if isinstance(agents, collections.Mapping):
        agents = agents['agents']
    return agents


def list_subnet_cidrs(client=None, **params):
    return [netaddr.IPNetwork(subnet['cidr'])
            for subnet in list_subnets(client=client, **params)]


def show_network(network, client=None, **params):
    return neutron_client(client).show_network(network, **params)['network']


def show_port(port, client=None, **params):
    return neutron_client(client).show_port(port, **params)['port']


def show_router(router, client=None, **params):
    return neutron_client(client).show_router(router, **params)['router']


def show_subnet(subnet, client=None, **params):
    return neutron_client(client).show_subnet(subnet, **params)['subnet']
