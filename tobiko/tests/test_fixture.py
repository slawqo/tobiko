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

import fixtures

import tobiko
from tobiko.tests import base


class MyFixtureClass(fixtures.Fixture):

    def _setUp(self):
        self.setup_executed = True
        self.addCleanup(self._cleanUp)

    def _cleanUp(self):
        self.cleanup_executed = True


MY_FIXTURE_NAME = __name__ + '.' + MyFixtureClass.__name__


class FixtureTypeTest(base.TobikoTest):

    def test_get_fixture_by_name(self):
        self._test_get_fixture(MY_FIXTURE_NAME, fixture_type=MyFixtureClass)

    def test_get_fixture_by_type(self):
        self._test_get_fixture(MyFixtureClass, fixture_type=MyFixtureClass)

    def _test_get_fixture(self, obj, fixture_type):
        fixture = tobiko.get_fixture(obj)
        self.assertIsInstance(fixture, fixture_type)
        self.assertIs(fixture, tobiko.get_fixture(obj))

    def test_get_name(self):
        fixture = tobiko.get_fixture(MY_FIXTURE_NAME)
        result = tobiko.get_fixture_name(fixture)
        self.assertEqual(MY_FIXTURE_NAME, result)

    def test_setup_fixture_by_name(self):
        self._test_setup_fixture(MY_FIXTURE_NAME)

    def test_setup_fixture_by_type(self):
        self._test_setup_fixture(MyFixtureClass)

    def _test_setup_fixture(self, obj):
        fixture = tobiko.get_fixture(obj)
        fixture.setup_executed = False

        tobiko.setup_fixture(obj)

        self.assertTrue(fixture.setup_executed)

    def test_cleanup_fixture_by_name(self):
        self._test_cleanup_fixture(MY_FIXTURE_NAME)

    def test_cleanup_fixture_by_type(self):
        self._test_cleanup_fixture(MyFixtureClass)

    def _test_cleanup_fixture(self, obj):
        fixture = tobiko.get_fixture(obj)
        fixture.setUp()

        tobiko.cleanup_fixture(obj)

        self.assertTrue(fixture.cleanup_executed)

    def test_list_required_fixtures_from_module(self):
        result = tobiko.list_required_fixtures([__name__])
        self.assertEqual([MY_FIXTURE_NAME], result)

    def test_list_required_fixtures_from_testcase_type(self):
        result = tobiko.list_required_fixtures([FixtureTypeTest])
        self.assertEqual([MY_FIXTURE_NAME], result)

    def test_list_required_fixtures_from_fixture_type(self):
        result = tobiko.list_required_fixtures([MyFixtureClass])
        self.assertEqual([MY_FIXTURE_NAME], result)

    def test_list_required_fixtures_from_fixture_name(self):
        result = tobiko.list_required_fixtures([MY_FIXTURE_NAME])
        self.assertEqual([MY_FIXTURE_NAME], result)

    def test_list_required_fixtures_from_method(
            self, fixture_type=MyFixtureClass):
        result = tobiko.list_required_fixtures([self.id()])
        self.assertEqual([MY_FIXTURE_NAME], result)
        self.assertIsInstance(tobiko.get_fixture(MY_FIXTURE_NAME),
                              fixture_type)

    def test_list_required_fixtures_from_fixture_object(self):
        fixture = tobiko.get_fixture(MY_FIXTURE_NAME)
        result = tobiko.list_required_fixtures([fixture])
        self.assertEqual([MY_FIXTURE_NAME], result)

    def test_setup_required_fixtures(self, fixture_type=MyFixtureClass):
        fixture = tobiko.get_fixture(fixture_type)
        fixture.setup_executed = False
        tobiko.setup_required_fixtures([self.id()])
        self.assertTrue(fixture.setup_executed)

    def test_cleanup_required_fixtures(self, fixture_type=MyFixtureClass):
        fixture = tobiko.get_fixture(fixture_type)
        fixture.cleanup_executed = False
        fixture.setUp()
        tobiko.cleanup_required_fixtures([self.id()])
        self.assertTrue(fixture.setup_executed)
        self.assertTrue(fixture.cleanup_executed)
