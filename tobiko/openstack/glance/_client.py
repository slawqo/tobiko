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
from glanceclient import exc

import tobiko
from tobiko.openstack import _client


class GlanceClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        return glanceclient.Client(session=session)


class GlanceClientManager(_client.OpenstackClientManager):

    def create_client(self, session):
        return GlanceClientFixture(session=session)


CLIENTS = GlanceClientManager()


def glance_client(obj=None):
    obj = obj or default_glance_client()
    if tobiko.is_fixture(obj):
        obj = tobiko.setup_fixture(obj).client
    return tobiko.check_valid_type(obj, glanceclient.Client)


def default_glance_client():
    return get_glance_client()


def get_glance_client(session=None, shared=True, init_client=None,
                      manager=None):
    manager = manager or CLIENTS
    fixture = manager.get_client(session=session, shared=shared,
                                 init_client=init_client)
    return glance_client(fixture)


def create_image(client=None, **params):
    """Look for the unique network matching some property values"""
    return glance_client(client).images.create(**params)


def delete_image(image_id, client=None, **params):
    try:
        glance_client(client).images.delete(image_id, **params)
    except exc.HTTPNotFound:
        return False
    else:
        return True


_RAISE_ERROR = object()


def get_image(image_id, client=None, default=_RAISE_ERROR):
    try:
        return glance_client(client).images.get(image_id=image_id)
    except exc.HTTPNotFound:
        if default is _RAISE_ERROR:
            raise
        else:
            return default


def find_image(client=None, unique=False, default=_RAISE_ERROR, **filters):
    """Look for an image matching some property values"""
    images = list_images(client=client, limit=2, **filters)
    if default is _RAISE_ERROR or images:
        if unique:
            return images.unique
        else:
            return images.first
    else:
        return default


def list_images(client=None, limit=None, **filters):
    images = glance_client(client).images.list(limit=limit, filters=filters)
    return tobiko.select(images)


def upload_image(image_id, image_data, client=None, **params):
    """Look for the unique network matching some property values"""
    return glance_client(client).images.upload(
        image_id=image_id, image_data=image_data, **params)
