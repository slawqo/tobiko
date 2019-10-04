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


def list_port_ip_addresses(port, subnet_id=None, ip_version=None,
                           check_connectivity=False, ssh_client=None):
    selected_addresses = []
    for fixed_ip in port['fixed_ips']:
        if subnet_id and subnet_id != fixed_ip['subnet_id']:
            continue
        ip_address = netaddr.IPAddress(fixed_ip['ip_address'])
        if ip_version and ip_version != ip_address.version:
            continue
        if check_connectivity and not ping.ping(
                host=ip_address, ssh_client=ssh_client).received:
            continue
        selected_addresses.append(ip_address)
    return tobiko.Selection(selected_addresses)


def find_port_ip_address(port, unique=False, **kwargs):
    addresses = list_port_ip_addresses(port=port, **kwargs)
    if unique:
        return addresses.unique
    else:
        return addresses.first
