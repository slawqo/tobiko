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

import metalsmith
import netaddr

import tobiko
from tobiko.shell import ping
from tobiko.shell import ssh
from tobiko.openstack.metalsmith import _client


MetalsmithInstance = typing.Union[metalsmith.Instance]


def list_instances(client: _client.MetalsmithClientType = None,
                   **params) \
        -> tobiko.Selection[MetalsmithInstance]:
    instances = tobiko.select(
        _client.metalsmith_client(client).list_instances())
    if params:
        instances = instances.with_attributes(**params)
    return instances


def find_instance(client: _client.MetalsmithClientType = None,
                  unique=False, **params) -> MetalsmithInstance:
    servers = list_instances(client=client, **params)
    if unique:
        return servers.unique
    else:
        return servers.first


def list_instance_ip_addresses(instance: MetalsmithInstance,
                               ip_version: int = None,
                               network_name: str = None,
                               check_connectivity=False,
                               ssh_client: ssh.SSHClientType = None)\
        -> tobiko.Selection[netaddr.IPAddress]:
    ip_addresses = tobiko.Selection[netaddr.IPAddress]()
    for _network, addresses in instance.ip_addresses().items():
        if network_name not in [None, _network]:
            continue

        for address in addresses:
            ip_address = netaddr.IPAddress(address)
            if ip_version not in [None, ip_address.version]:
                continue
            ip_addresses.append(ip_address)

    # check ICMP connectivity
    if check_connectivity:
        ip_addresses = ping.list_reachable_hosts(
            ip_addresses, ssh_client=ssh_client)

    return ip_addresses


def find_instance_ip_address(instance: MetalsmithInstance,
                             unique=False,
                             **params) -> netaddr.IPAddress:
    addresses = list_instance_ip_addresses(instance=instance, **params)
    if unique:
        return addresses.unique
    else:
        return addresses.first
