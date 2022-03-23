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

import typing

from designateclient.v2 import client

import tobiko
from tobiko.openstack import _client


DESIGNATE_CLIENT_CLASSES = client.Client,


class DesignateClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session) -> client.Client:
        return client.Client(session=session)


class DesignateClientManager(_client.OpenstackClientManager):

    def create_client(self, session) -> DesignateClientFixture:
        return DesignateClientFixture(session=session)


CLIENTS = DesignateClientManager()

DesignateClientType = typing.Union[client.Client, DesignateClientFixture]


def designate_client(obj: DesignateClientType = None):
    if obj is None:
        return get_designate_client()

    if isinstance(obj, client.Client):
        return obj

    fixture = tobiko.setup_fixture(obj)
    if isinstance(fixture, DesignateClientFixture):
        return fixture.client

    message = "Object {!r} is not an OctaviaClientFixture".format(obj)
    raise TypeError(message)


def get_designate_client(session=None,
                         shared=True,
                         init_client=None,
                         manager: DesignateClientManager = None) \
        -> client.Client:
    manager = manager or CLIENTS
    fixture = manager.get_client(session=session,
                                 shared=shared,
                                 init_client=init_client)
    tobiko.setup_fixture(fixture)
    return fixture.client
