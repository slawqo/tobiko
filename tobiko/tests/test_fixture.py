# Copyright 2018 Red Hat
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
from tobiko.tests import base


class TestFixture(tobiko.Fixture):

    def __init__(self):
        self.created = False
        self.deleted = False

    reset = __init__

    def create_fixture(self):
        self.created = True

    def delete_fixture(self):
        self.deleted = True


class FixtureTypeTest(base.TobikoTest):

    fixture_type = TestFixture
    fixture_name = __name__ + '.' + TestFixture.__name__

    @classmethod
    def setUpClass(cls):
        super(FixtureTypeTest, cls).setUpClass()
        cls.fixture = tobiko.get_fixture(cls.fixture_name)

    def setUp(self):
        super(FixtureTypeTest, self).setUp()
        self.fixture.reset()

    def test_fixture_type(self):
        self.assertIsInstance(self.fixture, self.fixture_type)

    def test_fixture_name(self):
        self.assertEqual(self.fixture_name, self.fixture.fixture_name)

    def test_get_fixture_by_name(self):
        self._test_get_fixture(self.fixture_name)

    def test_get_fixture_by_type(self):
        self._test_get_fixture(self.fixture_type)

    def _test_get_fixture(self, obj):
        fixture = tobiko.get_fixture(obj)
        self.assertIs(self.fixture, fixture)
        self.assertFalse(fixture.created)
        self.assertFalse(fixture.deleted)

    def test_create_fixture_by_name(self):
        self._test_create_fixture(self.fixture_name)

    def test_create_fixture_by_type(self):
        self._test_create_fixture(self.fixture_type)

    def _test_create_fixture(self, obj):
        fixture = tobiko.create_fixture(obj)
        self.assertIs(self.fixture, fixture)
        self.assertTrue(fixture.created)
        self.assertFalse(fixture.deleted)

    def test_delete_fixture_by_name(self):
        self._test_delete_fixture(self.fixture_name)

    def test_delete_fixture_by_type(self):
        self._test_delete_fixture(self.fixture_type)

    def _test_delete_fixture(self, obj=TestFixture):
        fixture = tobiko.delete_fixture(obj)
        self.assertIs(self.fixture, fixture)
        self.assertFalse(fixture.created)
        self.assertTrue(fixture.deleted)
