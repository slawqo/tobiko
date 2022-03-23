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

from tobiko.openstack import designate
from tobiko.tests.unit import openstack


class DesignateZoneTest(openstack.OpenstackTest):

    def test_designate_zone_id_with_str(self):
        self.assertEqual('some-id',
                         designate.designate_zone_id('some-id'))

    def test_designate_zone_id_with_dict(self):
        self.assertEqual('some-id',
                         designate.designate_zone_id({'id': 'some-id'}))
