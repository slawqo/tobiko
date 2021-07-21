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

import collections
import re
import typing

import tobiko
from tobiko.openstack.neutron import _client


# Agent binary names
DHCP_AGENT = 'neutron-dhcp-agent'
L3_AGENT = 'neutron-l3-agent'
METADATA_AGENT = 'neutron-metadata-agent'
OPENVSWITCH_AGENT = 'neutron-openvswitch-agent'
OVN_CONTROLLER = 'ovn-controller'
# NOTE(slaweq) name 'networking-ovn-metadata-agent' was used up to stable/train
# release when ovn driver was stadium project,
# Since stable/ussuri, when driver was included in the Neutron repo, it is
# called 'neutron-ovn-metadata-agent'
OVN_METADATA_AGENT = 'networking-ovn-metadata-agent'
NEUTRON_OVN_METADATA_AGENT = 'neutron-ovn-metadata-agent'


class AgentNotFoundOnHost(tobiko.TobikoException):
    message = "Agent {agent_type!s} not found on the host {host!s}"


NeutronAgentType = typing.Dict[str, typing.Any]


def list_agents(client=None, **params) \
        -> tobiko.Selection[NeutronAgentType]:
    agents = _client.neutron_client(client).list_agents(**params)
    if isinstance(agents, collections.Mapping):
        agents = agents['agents']
    return tobiko.Selection[NeutronAgentType](agents)


def list_l3_agent_hosting_routers(router, client=None, **params):
    agents = _client.neutron_client(client).list_l3_agent_hosting_routers(
        router, **params)
    if isinstance(agents, collections.Mapping):
        agents = agents['agents']
    return tobiko.select(agents)


def find_l3_agent_hosting_router(router, client=None, unique=False,
                                 **list_params):
    agents = list_l3_agent_hosting_routers(router=router, client=client,
                                           **list_params)
    if unique:
        return agents.unique
    else:
        return agents.first


def list_dhcp_agent_hosting_network(network, client=None, **params):
    agents = _client.neutron_client(client).list_dhcp_agent_hosting_networks(
        network, **params)
    if isinstance(agents, collections.Mapping):
        agents = agents['agents']
    return tobiko.select(agents)


class NetworkingAgentFixture(tobiko.SharedFixture):

    agents = None

    def setup_fixture(self):
        self.agents = list_agents()


def list_networking_agents(**attributes):
    return tobiko.setup_fixture(
        NetworkingAgentFixture).agents.with_items(**attributes)


def count_networking_agents(**params) -> int:
    return len(list_networking_agents(**params))


def missing_networking_agents(count=1, **params) -> int:
    actual_count = count_networking_agents(**params)
    return max(0, count - actual_count)


def has_networking_agents(**params) -> bool:
    return count_networking_agents(**params) > 0


def has_ovn() -> bool:
    return not has_ovs()


def has_ovs() -> bool:
    return has_networking_agents(binary=OPENVSWITCH_AGENT)


DecoratorType = typing.Callable[[typing.Union[typing.Callable, typing.Type]],
                                typing.Union[typing.Callable, typing.Type]]


AgentBinaryType = typing.Union[str, typing.Pattern[str]]


def skip_if_missing_networking_agents(
        binary: AgentBinaryType = None,
        count: int = 1,
        **params) \
        -> DecoratorType:
    if binary is not None:
        params['binary'] = binary
    message = "missing {return_value!r} agent(s)"
    if params:
        message += " with {!s}".format(
            ', '.join("{!s}={!r}".format(k, v) for k, v in params.items()))
    return tobiko.skip_if(message, missing_networking_agents, count=count,
                          **params)


def skip_unless_missing_networking_agents(
        binary: AgentBinaryType = None,
        count: int = 1,
        **params) \
        -> DecoratorType:
    if binary is not None:
        params['binary'] = binary
    message = "found {return_value!r} agent(s)"
    if params:
        message += " with {!s}".format(
            ', '.join("{!s}={!r}".format(k, v) for k, v in params.items()))
    return tobiko.skip_unless(message, missing_networking_agents, count=count,
                              **params)


def skip_if_is_old_ovn():
    """Skip the test if OVN is not configured"""
    binary = re.compile(f'({OPENVSWITCH_AGENT}|{OVN_CONTROLLER})')
    return skip_if_missing_networking_agents(binary)


def skip_unless_is_ovn():
    """Skip the test if OVN is not configured"""
    return skip_unless_missing_networking_agents(OPENVSWITCH_AGENT)


def skip_unless_is_ovs():
    """Skip the test if openvswitch agent does exist"""
    return skip_if_missing_networking_agents(OPENVSWITCH_AGENT)
