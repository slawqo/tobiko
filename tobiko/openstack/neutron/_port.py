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

from collections import abc
import typing

import netaddr

import tobiko
from tobiko.openstack.neutron import _client
from tobiko.openstack.neutron import _network
from tobiko.openstack.neutron import _subnet
from tobiko.shell import ssh
from tobiko.shell import ping


PortType = typing.Dict[str, typing.Any]
PortIdType = typing.Union[str, PortType]


def get_port_id(port: PortIdType) -> str:
    if isinstance(port, str):
        return port
    else:
        return port['id']


def get_port(port: PortIdType,
             client: _client.NeutronClientType = None,
             **params) -> PortType:
    port_id = get_port_id(port)
    try:
        return _client.neutron_client(client).show_port(
            port_id, **params)['port']
    except _client.NotFound as ex:
        raise NoSuchPort(id=port_id) from ex


def create_port(client: _client.NeutronClientType = None,
                network: _network.NetworkIdType = None,
                add_cleanup=True,
                **params) -> PortType:
    if 'network_id' not in params:
        if network is None:
            from tobiko.openstack import stacks
            network_id = tobiko.setup_fixture(
                stacks.NetworkStackFixture).network_id
        else:
            network_id = _network.get_network_id(network)
        params['network_id'] = network_id
    port = _client.neutron_client(client).create_port(
        body={'port': params})['port']
    if add_cleanup:
        tobiko.add_cleanup(cleanup_port, port=port, client=client)
    return port


def cleanup_port(port: PortIdType,
                 client: _client.NeutronClientType = None):
    try:
        delete_port(port=port, client=client)
    except NoSuchPort:
        pass


def update_port(port: PortIdType,
                client: _client.NeutronClientType = None,
                **params) -> PortType:
    port_id = get_port_id(port)
    reply = _client.neutron_client(client).update_port(port_id,
                                                       body={'port': params})
    return reply['port']


def delete_port(port: PortIdType,
                client: _client.NeutronClientType = None):
    port_id = get_port_id(port)
    try:
        _client.neutron_client(client).delete_port(port_id)
    except _client.NotFound as ex:
        raise NoSuchPort(id=port_id) from ex


DeviceIdType = typing.Union[str, typing.Any]


def get_device_id(device: DeviceIdType) -> str:
    if isinstance(device, str):
        return device
    elif isinstance(device, abc.Mapping):
        return device['id']
    elif hasattr(device, 'id'):
        return getattr(device, 'id')
    else:
        raise TypeError(f'{device!r} is not a valid device type')


def list_ports(client: _client.NeutronClientType = None,
               device: DeviceIdType = None,
               network: _network.NetworkIdType = None,
               subnet: _subnet.SubnetIdType = None,
               **params) -> tobiko.Selection[PortType]:
    if device is not None:
        params.setdefault('device_id', get_device_id(device))
    if network is not None:
        params.setdefault('network_id', _network.get_network_id(network))
    if subnet is not None:
        subnet_id = _subnet.get_subnet_id(subnet)
        params.setdefault('fixed_ips', f'subnet_id={subnet_id}')
    ports = _client.neutron_client(client).list_ports(**params)['ports']
    return tobiko.select(ports)


def find_port(client: _client.NeutronClientType = None,
              unique=False,
              default: PortType = None,
              **params):
    """Look for a port matching some property values"""
    ports = list_ports(client=client, **params)
    if default is None or ports:
        if unique:
            return ports.unique
        else:
            return ports.first
    else:
        return default


def list_port_ip_addresses(port: PortType,
                           subnet: _subnet.SubnetIdType = None,
                           ip_version: int = None,
                           check_connectivity: bool = False,
                           ssh_client: ssh.SSHClientFixture = None) -> \
        tobiko.Selection[netaddr.IPAddress]:
    if subnet is not None:
        subnet = _subnet.get_subnet_id(subnet)
    addresses = tobiko.Selection[netaddr.IPAddress](
        netaddr.IPAddress(fixed_ip['ip_address'])
        for fixed_ip in port['fixed_ips']
        if subnet is None or subnet == fixed_ip['subnet_id'])
    if ip_version is not None:
        addresses = addresses.with_attributes(version=ip_version)
    if addresses and check_connectivity:
        hosts = ping.list_reachable_hosts(addresses, ssh_client=ssh_client)
        addresses = tobiko.Selection(netaddr.IPAddress(host) for host in hosts)
    return addresses


def find_port_ip_address(port: PortType,
                         subnet: _subnet.SubnetIdType = None,
                         ip_version: int = None,
                         check_connectivity: bool = False,
                         ssh_client: ssh.SSHClientFixture = None,
                         unique: bool = False) -> netaddr.IPAddress:
    addresses = list_port_ip_addresses(port=port,
                                       subnet=subnet,
                                       ip_version=ip_version,
                                       check_connectivity=check_connectivity,
                                       ssh_client=ssh_client)
    if unique:
        return addresses.unique
    else:
        return addresses.first


def list_device_ip_addresses(device: DeviceIdType,
                             network: _network.NetworkIdType = None,
                             ip_version: int = None,
                             check_connectivity: bool = False,
                             ssh_client: ssh.SSHClientFixture = None,
                             need_dhcp: bool = None,
                             client: _client.NeutronClientType = None,
                             **subnet_params) -> \
        tobiko.Selection[netaddr.IPAddress]:
    ports = list_ports(device=device,
                       network=network,
                       client=client)
    if need_dhcp is not None:
        subnet_params['enable_dhcp'] = bool(need_dhcp)
    subnets = _subnet.list_subnets(network=network,
                                   ip_version=ip_version,
                                   client=client,
                                   **subnet_params)
    addresses = tobiko.Selection[netaddr.IPAddress](
        port_ip
        for subnet in subnets
        for port in ports
        for port_ip in list_port_ip_addresses(port=port,
                                              subnet=subnet,
                                              ip_version=ip_version))
    if addresses and check_connectivity:
        hosts = ping.list_reachable_hosts(addresses, ssh_client=ssh_client)
        addresses = tobiko.Selection(netaddr.IPAddress(host) for host in hosts)
    return addresses


def find_device_ip_address(device: DeviceIdType,
                           network: _network.NetworkIdType,
                           ip_version: int = None,
                           check_connectivity: bool = False,
                           ssh_client: ssh.SSHClientFixture = None,
                           need_dhcp: bool = None,
                           client: _client.NeutronClientType = None,
                           unique: bool = False,
                           **subnet_params) -> netaddr.IPAddress:
    addresses = list_device_ip_addresses(device=device,
                                         network=network,
                                         ip_version=ip_version,
                                         check_connectivity=check_connectivity,
                                         ssh_client=ssh_client,
                                         need_dhcp=need_dhcp,
                                         client=client,
                                         **subnet_params)
    if unique:
        return addresses.unique
    else:
        return addresses.first


class NoSuchPort(tobiko.ObjectNotFound):
    message = "No such port found for {id!r}"
