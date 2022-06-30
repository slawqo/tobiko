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

import netaddr

import tobiko
from tobiko.openstack import nova
from tobiko.openstack import neutron
from tobiko.shiftstack import _keystone


def shiftstack_neutron_client(obj: neutron.NeutronClientType) \
        -> neutron.NeutronClient:
    if obj is None:
        return get_shiftstack_neutron_client()
    else:
        return tobiko.check_valid_type(obj, neutron.NeutronClient)


def get_shiftstack_neutron_client() -> neutron.NeutronClient:
    session = _keystone.shiftstack_keystone_session()
    return neutron.get_neutron_client(session=session)


def list_shiftstack_node_ip_addresses(
        server: nova.ServerType,
        ip_version: int = None,
        client: neutron.NeutronClientType = None) \
        -> tobiko.Selection[netaddr.IPAddress]:
    client = shiftstack_neutron_client(client)
    return neutron.list_device_ip_addresses(device=server,
                                            ip_version=ip_version,
                                            client=client)


def find_shiftstack_node_ip_address(
        server: nova.ServerType,
        ip_version: int = None,
        client: neutron.NeutronClientType = None,
        unique=False) -> netaddr.IPAddress:
    addresses = list_shiftstack_node_ip_addresses(server=server,
                                                  ip_version=ip_version,
                                                  client=client)
    if unique:
        return addresses.unique
    else:
        return addresses.first
