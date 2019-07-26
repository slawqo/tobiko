# Copyright (c) 2019 Red Hat, Inc.
#
# All Rights Reserved.
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

import testtools

import tobiko
from tobiko.openstack import glance
from tobiko.openstack import stacks


class GlanceApiTestCase(testtools.TestCase):
    """Tests glance images API"""

    #: Stack of resources with a network with a gateway router
    fixture = tobiko.required_setup_fixture(stacks.CirrosImageFixture)

    def test_get_image(self):
        image = glance.get_image(self.fixture.image_id)
        self.assertEqual(self.fixture.image_id, image['id'])

    def test_find_image_by_id(self):
        image = glance.find_image(id=self.fixture.image_id)
        self.assertEqual(self.fixture.image_id, image['id'])

    def test_find_image_by_name(self):
        image = glance.find_image(name=self.fixture.image_name)
        self.assertEqual(self.fixture.image_name, image['name'])
