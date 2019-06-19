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
from tobiko.openstack.glance import _client
from tobiko.openstack import _find


class GlanceImageFixture(tobiko.SharedFixture):

    client = None
    image = None
    image_details = None

    def __init__(self, client=None, image=None):
        super(GlanceImageFixture, self).__init__()
        if client:
            self.client = client
        if image:
            self.image = image
        elif not self.image:
            self.image = self.fixture_name

    def setup_fixture(self):
        self.setup_client()
        self.setup_image()

    def setup_client(self):
        self.client = _client.glance_client(self.client)

    def setup_image(self):
        try:
            self.image_details = _client.find_image(self.image,
                                                    client=self.client)
        except _find.ResourceNotFound:
            self.image_details = self.create_image()

    def create_image(self):
        raise NotImplementedError

    @property
    def image_id(self):
        return self.image_details['id']

    @property
    def image_name(self):
        return self.image_details['name']
