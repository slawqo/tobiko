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
import typing

import netaddr
from neutronclient.v2_0 import client as neutronclient

import tobiko
from tobiko.openstack import _client


ServiceUnavailable = neutronclient.exceptions.ServiceUnavailable


class NeutronClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        return neutronclient.Client(session=session)


class NeutronClientManager(_client.OpenstackClientManager):

    def create_client(self, session):
        return NeutronClientFixture(session=session)


CLIENTS = NeutronClientManager()


NeutronClientType = typing.Union[None,
                                 neutronclient.Client,
                                 NeutronClientFixture]


def neutron_client(obj: NeutronClientType) -> neutronclient.Client:
    if not obj:
        return get_neutron_client()

    if isinstance(obj, neutronclient.Client):
        return obj

    fixture = tobiko.setup_fixture(obj)
    if isinstance(fixture, NeutronClientFixture):
        return fixture.client

    message = "Object {!r} is not a NeutronClientFixture".format(obj)
    raise TypeError(message)


class HasNeutronClientFixture(tobiko.SharedFixture):

    client: typing.Optional[neutronclient.Client] = None

    def __init__(self, obj: NeutronClientType = None):
        super(HasNeutronClientFixture, self).__init__()
        self._obj = obj

    def setup_fixture(self):
        self.client = neutron_client(self._obj)


def get_neutron_client(session=None, shared=True, init_client=None,
                       manager=None) -> neutronclient.Client:
    manager = manager or CLIENTS
    client = manager.get_client(session=session, shared=shared,
                                init_client=init_client)
    tobiko.setup_fixture(client)
    return client.client


_RAISE_ERROR = object()


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


def list_ports(client=None, **params):
    ports = neutron_client(client).list_ports(**params)['ports']
    return tobiko.select(ports)


NeutronSubnetType = typing.Dict[str, typing.Any]


def list_subnets(client=None, ip_version: typing.Optional[int] = None,
                 **params) -> tobiko.Selection[NeutronSubnetType]:
    if ip_version is not None:
        params['ip_version'] = ip_version
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


def get_floating_ip(floating_ip, client=None, **params):
    floating_ip = neutron_client(client).show_floatingip(floating_ip, **params)
    return floating_ip['floatingip']


def get_port(port, client=None, **params):
    try:
        return neutron_client(client).show_port(port, **params)['port']
    except neutronclient.exceptions.NotFound as ex:
        raise NoSuchPort(id=port) from ex


def get_router(router, client=None, **params):
    try:
        return neutron_client(client).show_router(router, **params)['router']
    except neutronclient.exceptions.NotFound as ex:
        raise NoSuchRouter(id=router) from ex


def get_subnet(subnet, client=None, **params):
    try:
        return neutron_client(client).show_subnet(subnet, **params)['subnet']
    except neutronclient.exceptions.NotFound as ex:
        raise NoSuchSubnet(id=subnet) from ex


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


def list_dhcp_agent_hosting_network(network, client=None, **params):
    agents = neutron_client(client).list_dhcp_agent_hosting_networks(
        network, **params)
    if isinstance(agents, collections.Mapping):
        agents = agents['agents']
    return tobiko.select(agents)


class NoSuchPort(tobiko.ObjectNotFound):
    message = "No such port found for {id!r}"


class NoSuchRouter(tobiko.ObjectNotFound):
    message = "No such router found for {id!r}"


class NoSuchSubnet(tobiko.ObjectNotFound):
    message = "No such subnet found for {id!r}"
