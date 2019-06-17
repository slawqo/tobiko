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

from novaclient import client as novaclient

import tobiko
from tobiko.openstack import _client


class NovaClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        return novaclient.Client('2', session=session)


class NovaClientManager(_client.OpenstackClientManager):

    def create_client(self, session):
        return NovaClientFixture(session=session)


CLIENTS = NovaClientManager()


def nova_client(obj):
    if not obj:
        return get_nova_client()

    if isinstance(obj, novaclient.Client):
        return obj

    fixture = tobiko.setup_fixture(obj)
    if isinstance(fixture, NovaClientFixture):
        return fixture.client

    message = "Object {!r} is not a NovaClientFixture".format(obj)
    raise TypeError(message)


def get_nova_client(session=None, shared=True, init_client=None,
                    manager=None):
    manager = manager or CLIENTS
    client = manager.get_client(session=session, shared=shared,
                                init_client=init_client)
    tobiko.setup_fixture(client)
    return client.client
