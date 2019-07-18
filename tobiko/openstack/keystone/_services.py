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
from tobiko.openstack.keystone import _client


class ServiceListFixture(tobiko.SharedFixture):

    client = None
    services = None

    def setup_fixture(self):
        self.services = _client.list_services()

    def has_service(self, **params):
        try:
            _client.find_resource(self.services,
                                  check_found=True,
                                  check_unique=False,
                                  **params)
        except _client.KeystoneResourceNotFound:
            return False
        else:
            return True


def has_service(**params):
    fixture = tobiko.setup_fixture(ServiceListFixture)
    return fixture.has_service(**params)


def is_service_missing(**params):
    return not has_service(**params)


def skip_if_missing_service(**params):
    return tobiko.skip_if('missing service: {!r}'.format(params),
                          is_service_missing, **params)
