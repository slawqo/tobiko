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

import tobiko
from tobiko.openstack.nova import _client


class HypervisorListFixture(tobiko.SharedFixture):

    client = None
    hypervisors = None

    def setup_fixture(self):
        self.setup_client()
        self.get_hypervisors()

    def setup_client(self):
        self.client = _client.get_nova_client()

    def get_hypervisors(self):
        self.hypervisors = _client.list_hypervisors(client=self.client)


def get_hypervisors(**params):
    hypervisors = tobiko.setup_fixture(HypervisorListFixture).hypervisors
    return tobiko.select(hypervisors).with_attributes(**params)


def missing_hypervisors(count=1, **params):
    agents = get_hypervisors(**params)
    return max(0, count - len(agents))


def skip_if_missing_hypervisors(count=1, **params):
    message = "missing {return_value!r} hypervisor(s)"
    if params:
        message += " with {!s}".format(
            ', '.join("{!s}={!r}".format(k, v) for k, v in params.items()))
    return tobiko.skip_if(message, missing_hypervisors, count=count,
                          **params)


def get_same_host_hypervisors(servers, hypervisor):
    host_hypervisors = get_servers_hypervisors(servers)
    same_host_server_ids = host_hypervisors.pop(hypervisor, None)
    if same_host_server_ids:
        return {hypervisor: same_host_server_ids}
    else:
        return {}


def get_different_host_hypervisors(servers, hypervisor):
    host_hypervisors = get_servers_hypervisors(servers)
    host_hypervisors.pop(hypervisor, None)
    return host_hypervisors


def get_servers_hypervisors(servers, client=None):
    hypervisors = collections.defaultdict(list)
    for server in (servers or list()):
        client = _client.nova_client(client)
        if isinstance(server, str):
            server_id = server
            server = _client.get_server(server_id, client=client)
        else:
            server_id = server.id
        hypervisor = get_server_hypervisor(server)
        hypervisors[hypervisor].append(server_id)
    return hypervisors


def get_server_hypervisor(server, client=None):
    if isinstance(server, str):
        server = _client.get_server(server, client=client)
    return getattr(server, 'OS-EXT-SRV-ATTR:host')
