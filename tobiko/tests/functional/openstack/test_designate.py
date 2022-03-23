# Copyright (c) 2022 Red Hat, Inc.
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

from collections import abc

import testtools

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import designate
from tobiko.openstack import stacks


@keystone.skip_unless_has_keystone_credentials()
@keystone.skip_if_missing_service(name='designate')
class DesignateClientTest(testtools.TestCase):

    stack = tobiko.required_fixture(stacks.DesignateZoneStackFixture)

    def test_get_designate_client(self):
        client = designate.get_designate_client()
        self.assertIsInstance(client, designate.DESIGNATE_CLIENT_CLASSES)

    def test_get_designate_zone(self):
        zone = designate.get_designate_zone(self.stack.zone_id)
        self.assertIsInstance(zone, abc.Mapping)
        self.assertEqual(zone['id'], self.stack.zone_id)
        self.assertEqual(zone['name'], self.stack.zone_name)
        self.assertEqual(zone, self.stack.zone_details)
