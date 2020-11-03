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

import typing  # noqa

import tobiko
from tobiko.openstack.neutron import _client


# Agent binary names
DHCP_AGENT = 'neutron-dhcp-agent'
L3_AGENT = 'neutron-l3-agent'
METADATA_AGENT = 'neutron-metadata-agent'
OPENVSWITCH_AGENT = 'neutron-openvswitch-agent'
OVN_CONTROLLER = 'ovn-controller'
OVN_METADATA_AGENT = 'networking-ovn-metadata-agent'


class AgentNotFoundOnHost(tobiko.TobikoException):
    message = ("Agent {agent_type!s} not found on the host {host!s}")


class NetworkingAgentFixture(tobiko.SharedFixture):

    agents = None

    def setup_fixture(self):
        self.agents = _client.list_agents()


def list_networking_agents(**attributes):
    return tobiko.setup_fixture(
        NetworkingAgentFixture).agents.with_items(**attributes)


def missing_networking_agents(count=1, **params):
    agents = list_networking_agents(**params)
    return max(0, count - len(agents))


def has_networking_agents(count=1, **params):
    return not missing_networking_agents(count=count, **params)


DecoratorType = typing.Callable[[typing.Union[typing.Callable, typing.Type]],
                                typing.Union[typing.Callable, typing.Type]]


def skip_if_missing_networking_agents(binary: typing.Optional[str] = None,
                                      count: int = 1, **params) -> \
        DecoratorType:
    if binary is not None:
        params['binary'] = binary
    message = "missing {return_value!r} agent(s)"
    if params:
        message += " with {!s}".format(
            ', '.join("{!s}={!r}".format(k, v) for k, v in params.items()))
    return tobiko.skip_if(message, missing_networking_agents, count=count,
                          **params)


def skip_unless_is_ovn():
    '''Skip the test if OVN is not configured'''
    from tobiko.tripleo import overcloud
    from tobiko.tripleo import containers
    if overcloud.has_overcloud():
        message = "OVN is not configured"
        return tobiko.skip_unless(message, containers.ovn_used_on_overcloud)
    else:
        return skip_if_missing_networking_agents(OVN_CONTROLLER)


def skip_unless_is_ovs():
    '''Skip the test if openvswitch agent does not exist'''
    return skip_if_missing_networking_agents(OPENVSWITCH_AGENT)
