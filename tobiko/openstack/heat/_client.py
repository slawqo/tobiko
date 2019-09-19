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

from heatclient.v1 import client as heatclient

import tobiko
from tobiko.openstack import _client


class HeatClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        return heatclient.Client(session=session,
                                 endpoint_type='public',
                                 service_type='orchestration')


class HeatClientManager(_client.OpenstackClientManager):

    def create_client(self, session):
        return HeatClientFixture(session=session)


CLIENTS = HeatClientManager()


def heat_client(obj=None):
    if obj is None:
        return default_heat_client()

    if isinstance(obj, heatclient.Client):
        return obj

    fixture = tobiko.get_fixture(obj)
    if isinstance(fixture, HeatClientFixture):
        return tobiko.setup_fixture(fixture).client

    message = "Object {!r} is not a NeutronClientFixture".format(obj)
    raise TypeError(message)


def default_heat_client():
    return get_heat_client()


def get_heat_client(session=None, shared=True, init_client=None,
                    manager=None):
    manager = manager or CLIENTS
    fixture = manager.get_client(session=session, shared=shared,
                                 init_client=init_client)
    return tobiko.setup_fixture(fixture).client
