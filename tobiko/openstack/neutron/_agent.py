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

import tobiko
from tobiko.openstack.neutron import _client


class NetworkingAgentFixture(tobiko.SharedFixture):

    client = None
    agents = None

    def setup_fixture(self):
        self.setup_client()
        self.get_agents()

    def setup_client(self):
        self.client = _client.get_neutron_client()

    def get_agents(self):
        self.agents = _client.list_agents(client=self.client)


def get_networking_agents(**attributes):
    agents = tobiko.setup_fixture(NetworkingAgentFixture).agents
    return agents.with_items(**attributes)


def missing_networking_agents(count=1, **params):
    agents = get_networking_agents(**params)
    return max(0, count - len(agents))


def has_networking_agents(count=1, **params):
    return not missing_networking_agents(count=count, **params)


def skip_if_missing_networking_agents(count=1, **params):
    message = "missing {return_value!r} agent(s)"
    if params:
        message += " with {!s}".format(
            ', '.join("{!s}={!r}".format(k, v) for k, v in params.items()))
    return tobiko.skip_if(message, missing_networking_agents, count=count,
                          **params)
