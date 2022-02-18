# Copyright (c) 2021 Red Hat, Inc.
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

from tobiko.shell import sh


class TestSystemctl(testtools.TestCase):

    def setUp(self):
        super().setUp()
        try:
            sh.execute('pgrep systemd')
        except sh.ShellCommandFailed:
            self.skipTest("systemd is not running")

    def test_list_system_services(self):
        units = sh.list_systemd_units()
        self.assertNotEqual([], units)

    def test_list_system_services_with_all(self):
        units = sh.list_systemd_units(all=True)
        self.assertNotEqual([], units)

    def test_list_system_services_with_state(self):
        units = sh.list_systemd_units(state='active')
        self.assertNotEqual([], units)
        self.assertEqual(units.with_attributes(active='active'), units)

    def test_list_system_services_with_type(self):
        units = sh.list_systemd_units(type='socket')
        self.assertNotEqual([], units)
