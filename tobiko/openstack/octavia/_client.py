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

from octaviaclient.api.v2 import octavia

import tobiko
from tobiko.openstack import _client
from tobiko.openstack import keystone


class OctaviaClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        keystone_client = keystone.get_keystone_client(session=session)
        endpoint = keystone.find_service_endpoint(name='octavia',
                                                  client=keystone_client)
        return octavia.OctaviaAPI(session=session, endpoint=endpoint.url)


class OctaviaClientManatger(_client.OpenstackClientManager):

    def create_client(self, session):
        return OctaviaClientFixture(session=session)


CLIENTS = OctaviaClientManatger()


def octavia_client(obj):
    if not obj:
        return get_octavia_client()

    if isinstance(obj, octavia.OctaviaAPI):
        return obj

    fixture = tobiko.setup_fixture(obj)
    if isinstance(fixture, OctaviaClientFixture):
        return fixture.client

    message = "Object {!r} is not an OctaviaClientFixture".format(obj)
    raise TypeError(message)


def get_octavia_client(session=None, shared=True, init_client=None,
                       manager=None):
    manager = manager or CLIENTS
    client = manager.get_client(session=session, shared=shared,
                                init_client=init_client)
    tobiko.setup_fixture(client)
    return client.client
