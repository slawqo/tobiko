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
from tobiko.openstack.neutron import _network


SERVER = 'neutron-server'
DHCP_AGENT = _agent.DHCP_AGENT
L3_AGENT = _agent.L3_AGENT
METADATA_AGENT = _agent.METADATA_AGENT
OPENVSWITCH_AGENT = _agent.OPENVSWITCH_AGENT
OVN_CONTROLLER = _agent.OVN_CONTROLLER
OVN_METADATA_AGENT = _agent.OVN_METADATA_AGENT
AgentNotFoundOnHost = _agent.AgentNotFoundOnHost
skip_if_missing_networking_agents = _agent.skip_if_missing_networking_agents
skip_unless_is_ovn = _agent.skip_unless_is_ovn
skip_unless_is_ovs = _agent.skip_unless_is_ovs
list_networking_agents = _agent.list_networking_agents

NeutronClientFixture = _client.NeutronClientFixture
ServiceUnavailable = _client.ServiceUnavailable
neutron_client = _client.neutron_client
get_neutron_client = _client.get_neutron_client
find_subnet = _client.find_subnet
find_port = _client.find_port
list_ports = _client.list_ports
list_subnets = _client.list_subnets
list_subnet_cidrs = _client.list_subnet_cidrs
list_agents = _client.list_agents
get_floating_ip = _client.get_floating_ip
get_router = _client.get_router
get_port = _client.get_port
get_subnet = _client.get_subnet
list_l3_agent_hosting_routers = _client.list_l3_agent_hosting_routers
find_l3_agent_hosting_router = _client.find_l3_agent_hosting_router
list_dhcp_agent_hosting_network = _client.list_dhcp_agent_hosting_network

NoSuchPort = _client.NoSuchPort
NoSuchRouter = _client.NoSuchRouter
NoSuchSubnet = _client.NoSuchSubnet

new_ipv4_cidr = _cidr.new_ipv4_cidr
new_ipv6_cidr = _cidr.new_ipv6_cidr

get_networking_extensions = _extension.get_networking_extensions
missing_networking_extensions = _extension.missing_networking_extensions
has_networking_extensions = _extension.has_networking_extensions

skip_if_missing_networking_extensions = (
    _extension.skip_if_missing_networking_extensions)

find_port_ip_address = _port.find_port_ip_address
list_port_ip_addresses = _port.list_port_ip_addresses
find_device_ip_address = _port.find_device_ip_address
list_device_ip_addresses = _port.list_device_ip_addresses

NeutronNetworkFixture = _network.NeutronNetworkFixture
NoSuchNetwork = _network.NoSuchNetwork
create_network = _network.create_network
delete_network = _network.delete_network
get_network = _network.get_network
find_network = _network.find_network
list_networks = _network.list_networks
list_network_nameservers = _network.list_network_nameservers
