# Copyright 2020 Red Hat
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
from tobiko.tests import unit


class UtilsTests(unit.TobikoUnitTest):

    def test_get_short_hostname(self):
        self.assertEqual("testhost", tobiko.get_short_hostname("testhost"))
        self.assertEqual("testhost", tobiko.get_short_hostname("TesTHoSt"))
        self.assertEqual(
            "testhost", tobiko.get_short_hostname("testhost.domain"))
        self.assertEqual(
            "testhost", tobiko.get_short_hostname("teSthOsT.dOmAin"))
        self.assertEqual("testhost", tobiko.get_short_hostname("testhost."))
        self.assertEqual("testhost", tobiko.get_short_hostname("TesTHoSt."))
