# Copyright 2022 Red Hat
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

import metalsmith
from oslo_log import log

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import _client


LOG = log.getLogger(__name__)


CLIENT_CLASSES = (metalsmith.Provisioner,)
MetalsmithClient = typing.Union[metalsmith.Provisioner]


class MetalsmithClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session) -> MetalsmithClient:
        return metalsmith.Provisioner(session=session)


class MetalsmithClientManager(_client.OpenstackClientManager):

    def create_client(self, session) -> MetalsmithClientFixture:
        return MetalsmithClientFixture(session=session)


CLIENTS = MetalsmithClientManager()


def metalsmith_client_manager(manager: MetalsmithClientManager = None) \
        -> MetalsmithClientManager:
    if manager is None:
        manager = CLIENTS
    return manager


MetalsmithClientType = typing.Union[
    MetalsmithClient,
    MetalsmithClientFixture,
    typing.Type[MetalsmithClientFixture]]


def metalsmith_client(obj: MetalsmithClientType = None) \
        -> MetalsmithClient:
    if obj is None:
        return get_metalsmith_client()

    if isinstance(obj, CLIENT_CLASSES):
        return obj

    fixture = tobiko.setup_fixture(obj)
    if isinstance(fixture, MetalsmithClientFixture):
        assert fixture.client is not None
        return fixture.client

    message = f"Object '{obj}' is not a MetalsmithProvisionerFixture"
    raise TypeError(message)


def get_metalsmith_client(session: keystone.KeystoneSessionType = None,
                          shared=True,
                          init_client=None,
                          manager: MetalsmithClientManager = None) \
        -> MetalsmithClient:
    manager = metalsmith_client_manager(manager)
    client = manager.get_client(session=session,
                                shared=shared,
                                init_client=init_client)
    tobiko.setup_fixture(client)
    return client.client
