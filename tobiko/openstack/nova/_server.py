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

from oslo_log import log
import netaddr

import tobiko
from tobiko.shell import ping


LOG = log.getLogger(__name__)


def list_server_ip_addresses(server, network_name=None, ip_version=None,
                             address_type=None, check_connectivity=False,
                             ssh_client=None):
    selected_addresses = []
    for _network_name, addresses in server.addresses.items():
        # check network name
        if network_name and network_name != _network_name:
            continue

        for address in addresses:
            # check IP address version
            _ip_version = address['version']
            if ip_version and ip_version != _ip_version:
                continue

            # check IP address type
            _address_type = address.get('OS-EXT-IPS:type')
            if address_type and address_type != _address_type:
                if _address_type is None:
                    LOG.warning('Unable to get address type of address %r',
                                address)
                continue

            ip_address = netaddr.IPAddress(address['addr'],
                                           version=_ip_version)

            # check ICMP connectivity
            if check_connectivity and not ping.ping(
                    host=ip_address, ssh_client=ssh_client).received:
                continue

            selected_addresses.append(ip_address)

    return tobiko.Selection(selected_addresses)


def find_server_ip_address(server, unique=False, **kwargs):
    addresses = list_server_ip_addresses(server=server, **kwargs)
    if unique:
        return addresses.unique
    else:
        return addresses.first
