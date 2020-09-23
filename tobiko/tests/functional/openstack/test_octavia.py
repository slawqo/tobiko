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

from tobiko.openstack import keystone
from tobiko.openstack import octavia


@keystone.skip_unless_has_keystone_credentials()
@keystone.skip_if_missing_service(name='octavia')
class OctaviaClientAPITest(testtools.TestCase):

    def test_get_octava_client(self):
        client = octavia.get_octavia_client()
        self.assertIsInstance(client, octavia.OCTAVIA_CLIENT_CLASSSES)
