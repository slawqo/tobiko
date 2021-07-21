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


NeutronClientException = neutronclient.exceptions.NeutronClientException
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


def list_subnet_cidrs(client=None, **params):
    return tobiko.select(netaddr.IPNetwork(subnet['cidr'])
                         for subnet in list_subnets(client=client, **params))


def get_floating_ip(floating_ip, client=None, **params):
    try:
        floating_ip = neutron_client(client).show_floatingip(
                floating_ip, **params)
    except neutronclient.exceptions.NotFound as ex:
        raise NoSuchFIP(id=floating_ip) from ex
    return floating_ip['floatingip']


def create_floating_ip(floating_network_id=None, client=None, **params):
    if floating_network_id is None:
        from tobiko.openstack import stacks
        floating_network_id = tobiko.setup_fixture(
                stacks.FloatingNetworkStackFixture).external_id
    if floating_network_id is not None:
        params['floating_network_id'] = floating_network_id
    floating_ip = neutron_client(client).create_floatingip(
            body={'floatingip': params})
    return floating_ip['floatingip']


def delete_floating_ip(floating_ip, client=None):
    try:
        neutron_client(client).delete_floatingip(floating_ip)
    except neutronclient.exceptions.NotFound as ex:
        raise NoSuchFIP(id=floating_ip) from ex


def update_floating_ip(floating_ip, client=None, **params):
    fip = neutron_client(client).update_floatingip(
            floating_ip, body={'floatingip': params})
    return fip['floatingip']


def get_port(port, client=None, **params):
    try:
        return neutron_client(client).show_port(port, **params)['port']
    except neutronclient.exceptions.NotFound as ex:
        raise NoSuchPort(id=port) from ex


def create_port(client=None, **params):
    port = neutron_client(client).create_port(body={'port': params})
    return port['port']


def delete_port(port, client=None):
    try:
        neutron_client(client).delete_port(port)
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


class NoSuchPort(tobiko.ObjectNotFound):
    message = "No such port found for {id!r}"


class NoSuchRouter(tobiko.ObjectNotFound):
    message = "No such router found for {id!r}"


class NoSuchSubnet(tobiko.ObjectNotFound):
    message = "No such subnet found for {id!r}"


class NoSuchFIP(tobiko.ObjectNotFound):
    message = "No such floating IP found for {id!r}"
