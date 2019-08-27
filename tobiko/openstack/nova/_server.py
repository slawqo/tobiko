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

import netaddr

import tobiko
from tobiko.shell import ping


def list_server_ip_addresses(server, network_name=None, ip_version=None,
                             check_connectivity=False):
    selected_addresses = []
    for _network_name, addresses in server.addresses.items():
        if network_name and network_name != _network_name:
            continue
        for address in addresses:
            _ip_version = address['version']
            if ip_version and ip_version != _ip_version:
                continue
            ip_address = netaddr.IPAddress(address['addr'],
                                           version=_ip_version)
            if check_connectivity:
                if not ping.ping(host=ip_address).received:
                    continue
            selected_addresses.append(ip_address)
    return tobiko.Selection(selected_addresses)


def find_server_ip_address(server, network_name=None, ip_version=None,
                           check_connectivity=False, unique=False):
    addresses = list_server_ip_addresses(server=server,
                                         network_name=network_name,
                                         ip_version=ip_version,
                                         check_connectivity=check_connectivity)
    if unique:
        return addresses.unique
    else:
        return addresses.first
