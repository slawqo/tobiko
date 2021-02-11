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
from tobiko.shell import ssh
from tobiko.shell import ping


NeutronPortType = typing.Dict[str, typing.Any]


def list_port_ip_addresses(port: NeutronPortType,
                           subnet_id: typing.Optional[str] = None,
                           ip_version: typing.Optional[int] = None,
                           check_connectivity: bool = False,
                           ssh_client: ssh.SSHClientFixture = None) -> \
        tobiko.Selection[netaddr.IPAddress]:
    addresses = tobiko.Selection[netaddr.IPAddress](
        netaddr.IPAddress(fixed_ip['ip_address'])
        for fixed_ip in port['fixed_ips']
        if subnet_id is None or subnet_id == fixed_ip['subnet_id'])
    if ip_version:
        addresses = addresses.with_attributes(version=ip_version)
    if addresses and check_connectivity:
        hosts = ping.list_reachable_hosts(addresses, ssh_client=ssh_client)
        addresses = tobiko.Selection(netaddr.IPAddress(host) for host in hosts)
    return addresses


def find_port_ip_address(port: NeutronPortType, unique: bool = False,
                         **kwargs) -> netaddr.IPAddress:
    addresses = list_port_ip_addresses(port=port, **kwargs)
    if unique:
        return addresses.unique
    else:
        return addresses.first


def list_device_ip_addresses(device_id: str,
                             network_id: typing.Optional[str] = None,
                             ip_version: typing.Optional[int] = None,
                             check_connectivity: bool = False,
                             ssh_client: ssh.SSHClientFixture = None,
                             need_dhcp: typing.Optional[bool] = None,
                             **subnet_params) -> \
        tobiko.Selection[netaddr.IPAddress]:
    ports = _client.list_ports(device_id=device_id,
                               network_id=network_id)
    if need_dhcp is not None:
        subnet_params['enable_dhcp'] = bool(need_dhcp)
    subnets = _client.list_subnets(network_id=network_id,
                                   ip_version=ip_version,
                                   **subnet_params)
    addresses = tobiko.Selection[netaddr.IPAddress](
        port_ip
        for subnet in subnets
        for port in ports
        for port_ip in list_port_ip_addresses(port=port,
                                              subnet_id=subnet['id'],
                                              ip_version=ip_version))
    if addresses and check_connectivity:
        hosts = ping.list_reachable_hosts(addresses, ssh_client=ssh_client)
        addresses = tobiko.Selection(netaddr.IPAddress(host) for host in hosts)
    return addresses


def find_device_ip_address(device_id: str, unique: bool = False, **kwargs):
    addresses = list_device_ip_addresses(device_id=device_id,  **kwargs)
    if unique:
        return addresses.unique
    else:
        return addresses.first
