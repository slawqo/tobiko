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

from tobiko.openstack.neutron import _agent
from tobiko.openstack.neutron import _client
from tobiko.openstack.neutron import _cidr
from tobiko.openstack.neutron import _extension
from tobiko.openstack.neutron import _port


neutron_client = _client.neutron_client
get_neutron_client = _client.get_neutron_client
NeutronClientFixture = _client.NeutronClientFixture
find_network = _client.find_network
list_networks = _client.list_networks
find_subnet = _client.find_subnet
find_port = _client.find_port
list_ports = _client.list_ports
list_subnets = _client.list_subnets
list_subnet_cidrs = _client.list_subnet_cidrs
list_agents = _client.list_agents
get_network = _client.get_network
get_router = _client.get_router
get_port = _client.get_port
get_subnet = _client.get_subnet
list_agents_hosting_router = _client.list_agents_hosting_router

new_ipv4_cidr = _cidr.new_ipv4_cidr
new_ipv6_cidr = _cidr.new_ipv6_cidr

get_networking_extensions = _extension.get_networking_extensions
missing_networking_extensions = _extension.missing_networking_extensions
has_networking_extensions = _extension.has_networking_extensions

skip_if_missing_networking_extensions = (
    _extension.skip_if_missing_networking_extensions)
skip_if_missing_networking_agents = _agent.skip_if_missing_networking_agents

find_port_ip_address = _port.find_port_ip_address
list_port_ip_addresses = _port.list_port_ip_addresses
