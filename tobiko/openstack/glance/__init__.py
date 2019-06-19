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

from tobiko.openstack.glance import _client
from tobiko.openstack.glance import _image

glance_client = _client.glance_client
get_glance_client = _client.get_glance_client
GlanceClientFixture = _client.GlanceClientFixture
find_image = _client.find_image
list_images = _client.list_images

GlanceImageFixture = _image.GlanceImageFixture
