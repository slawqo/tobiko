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
    return tobiko.find_by_attributes(hypervisors, **params)


def missing_hypervisors(count=1, **params):
    agents = get_hypervisors(**params)
    return max(0, count - len(agents))


def has_networking_agents(count=1, **params):
    return not missing_hypervisors(count=count, **params)


def skip_if_missing_hypervisors(count=1, **params):
    message = "missing {return_value!r} hypervisor(s)"
    if params:
        message += " with {!s}".format(
            ', '.join("{!s}={!r}".format(k, v) for k, v in params.items()))
    return tobiko.skip_if(message, missing_hypervisors, count=count,
                          **params)
