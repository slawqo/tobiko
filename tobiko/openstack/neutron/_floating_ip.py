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

import tobiko
from tobiko.openstack.neutron import _client
from tobiko.openstack.neutron import _network
from tobiko.openstack.neutron import _port


FloatingIpType = typing.Dict[str, typing.Any]
FloatingIpIdType = typing.Union[str, FloatingIpType]


def get_floating_ip_id(floating_ip: FloatingIpIdType) -> str:
    if isinstance(floating_ip, str):
        return floating_ip
    else:
        return floating_ip['id']


def get_floating_ip(floating_ip: FloatingIpType,
                    client: _client.NeutronClientType = None,
                    **params):
    floating_ip_id = get_floating_ip_id(floating_ip)
    try:
        return _client.neutron_client(client).show_floatingip(
            floating_ip_id, **params)['floatingip']
    except _client.NotFound as ex:
        raise NoSuchFloatingIp(id=floating_ip_id) from ex


def find_floating_ip(client: _client.NeutronClientType = None,
                     unique=False,
                     default: FloatingIpType = None,
                     **params) -> FloatingIpType:
    """Look for a port matching some property values"""
    floating_ips = list_floating_ips(client=client, **params)
    if default is None or floating_ips:
        if unique:
            return floating_ips.unique
        else:
            return floating_ips.first
    else:
        return default


def list_floating_ips(client: _client.NeutronClientType = None,
                      retrieve_all=True,
                      port: _port.PortIdType = None,
                      **params) -> tobiko.Selection[FloatingIpType]:
    if port is not None:
        params['port_id'] = _port.get_port_id(port)
    floating_ips = _client.neutron_client(client).list_floatingips(
        retrieve_all=retrieve_all, **params)['floatingips']
    return tobiko.select(floating_ips)


def create_floating_ip(network: _network.NetworkIdType = None,
                       port: _port.PortIdType = None,
                       client: _client.NeutronClientType = None,
                       add_cleanup=True,
                       **params) -> FloatingIpType:
    if network is None:
        network = params.get('floating_network_id')
        if network is None:
            from tobiko.openstack import stacks
            network = stacks.get_floating_network_id()
    params['floating_network_id'] = _network.get_network_id(network)
    if port is not None:
        params['port_id'] = _port.get_port_id(port)
    floating_ip: FloatingIpType = _client.neutron_client(
        client).create_floatingip(body={'floatingip': params})['floatingip']
    if add_cleanup:
        tobiko.add_cleanup(cleanup_floating_ip,
                           floating_ip=floating_ip,
                           client=client)
    return floating_ip


def cleanup_floating_ip(floating_ip: FloatingIpIdType,
                        client: _client.NeutronClientType = None):
    try:
        delete_floating_ip(floating_ip=floating_ip,
                           client=client)
    except NoSuchFloatingIp:
        pass


def delete_floating_ip(floating_ip: FloatingIpIdType,
                       client: _client.NeutronClientType = None):
    floating_ip_id = get_floating_ip_id(floating_ip)
    try:
        _client.neutron_client(client).delete_floatingip(floating_ip_id)
    except _client.NotFound as ex:
        raise NoSuchFloatingIp(id=floating_ip_id) from ex


def update_floating_ip(floating_ip: FloatingIpIdType,
                       client: _client.NeutronClientType = None,
                       **params) -> FloatingIpType:
    floating_ip_id = get_floating_ip_id(floating_ip)
    try:
        return _client.neutron_client(client).update_floatingip(
                floating_ip_id, body={'floatingip': params})['floatingip']
    except _client.NotFound as ex:
        raise NoSuchFloatingIp(id=floating_ip_id) from ex


class NoSuchFloatingIp(tobiko.ObjectNotFound):
    message = "No such floating IP found for {id!r}"
