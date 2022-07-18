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

import unittest

from packaging import version

import tobiko


class TestVersion(unittest.TestCase):

    def test_parse_version(self):
        self.assertEqual(version.parse('1.0.0'),
                         tobiko.parse_version('1'))
        self.assertEqual(version.parse('1.2.0'),
                         tobiko.parse_version('1.2'))
        self.assertEqual(version.parse('1.2.3'),
                         tobiko.parse_version('1.2.3'))
        self.assertEqual(version.parse('3.2.1'),
                         tobiko.parse_version(' a b c 10 3.2.1 25.2.1'))

    def test_parse_version_with_invalid(self):
        with self.assertRaises(tobiko.InvalidVersion):
            tobiko.parse_version('abc')

    def test_get_version_with_srt(self):
        self.assertEqual(version.parse('3.2.1'),
                         tobiko.get_version(' a b c 10 3.2.1 25.2.1'))

    def test_get_version_with_version(self):
        reference = version.parse('3.2.1')
        self.assertIs(reference,
                      tobiko.get_version(reference))

    def test_match_version_with_str(self):
        self.assertTrue(tobiko.match_version('1.2.3'))

    def test_match_version_with_version(self):
        reference = version.parse('3.2.1')
        self.assertTrue(tobiko.match_version(reference))

    def test_match_version_min_version(self):
        self.assertTrue(tobiko.match_version('1.0.0',
                                             min_version='0.9.9'))
        self.assertTrue(tobiko.match_version('1.0.0',
                                             min_version='1'))
        self.assertTrue(tobiko.match_version('1.0.0',
                                             min_version='1.0'))
        self.assertTrue(tobiko.match_version('1.0.0',
                                             min_version='1.0.0'))
        self.assertFalse(tobiko.match_version('1.0.0',
                                              min_version='1.0.1'))

    def test_match_version_max_version(self):
        self.assertFalse(tobiko.match_version('1.0.0',
                                              max_version='0.9.9'))
        self.assertFalse(tobiko.match_version('1.0.0',
                                              max_version='1.0.0'))
        self.assertTrue(tobiko.match_version('1.0.0',
                                             max_version='1.0.1'))
