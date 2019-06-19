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

from glanceclient.v2 import client as glanceclient

import tobiko
from tobiko.openstack import _client
from tobiko.openstack import _find


class GlanceClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        return glanceclient.Client(session=session)


class GlanceClientManager(_client.OpenstackClientManager):

    def create_client(self, session):
        return GlanceClientFixture(session=session)


CLIENTS = GlanceClientManager()


def glance_client(obj):
    if not obj:
        return get_glance_client()

    if isinstance(obj, glanceclient.Client):
        return obj

    fixture = tobiko.setup_fixture(obj)
    if isinstance(fixture, GlanceClientFixture):
        return fixture.client

    message = "Object {!r} is not a NovaClientFixture".format(obj)
    raise TypeError(message)


def get_glance_client(session=None, shared=True, init_client=None,
                      manager=None):
    manager = manager or CLIENTS
    client = manager.get_client(session=session, shared=shared,
                                init_client=init_client)
    tobiko.setup_fixture(client)
    return client.client


def find_image(obj=None, properties=None, client=None, **params):
    """Look for the unique network matching some property values"""
    return _find.find_resource(
        obj=obj, resource_type='image', properties=properties,
        resources=list_images(client=client, **params), **params)


def list_images(client=None, **params):
    return list(glance_client(client).images.list(**params))
