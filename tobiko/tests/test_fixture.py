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

import mock

import tobiko
from tobiko.tests import unit


class MyFixture(tobiko.SharedFixture):

    def __init__(self):
        super(MyFixture, self).__init__()
        self.setup_fixture = mock.MagicMock(
            specs=tobiko.SharedFixture.setup_fixture)
        self.cleanup_fixture = mock.MagicMock(
            specs=tobiko.SharedFixture.cleanup_fixture)


MY_FIXTURE_NAME = __name__ + '.' + MyFixture.__name__


class FixtureManagerTest(unit.TobikoUnitTest):

    def setUp(self):
        super(FixtureManagerTest, self).setUp()
        tobiko.remove_fixture(MyFixture)

    def test_get_fixture_by_name(self):
        self._test_get_fixture(MY_FIXTURE_NAME, fixture_type=MyFixture)

    def test_get_fixture_by_type(self):
        self._test_get_fixture(MyFixture, fixture_type=MyFixture)

    def _test_get_fixture(self, obj, fixture_type):
        fixture = tobiko.get_fixture(obj)
        self.assertIsInstance(fixture, fixture_type)
        self.assertIs(fixture, tobiko.get_fixture(obj))
        self.assertIs(fixture, tobiko.get_fixture(MY_FIXTURE_NAME))

    def test_remove_fixture_by_name(self):
        self._test_remove_fixture(MY_FIXTURE_NAME)

    def test_remove_fixture_by_type(self):
        self._test_remove_fixture(MyFixture)

    def _test_remove_fixture(self, obj):
        fixture = tobiko.get_fixture(obj)

        result = tobiko.remove_fixture(obj)

        self.assertIs(fixture, result)
        self.assertIsNot(fixture, tobiko.get_fixture(obj))

    def test_get_name(self):
        fixture = tobiko.get_fixture(MY_FIXTURE_NAME)
        result = tobiko.get_fixture_name(fixture)
        self.assertEqual(MY_FIXTURE_NAME, result)

    def test_setup_fixture_by_name(self):
        self._test_setup_fixture(MY_FIXTURE_NAME)

    def test_setup_fixture_by_type(self):
        self._test_setup_fixture(MyFixture)

    def _test_setup_fixture(self, obj):
        result = tobiko.setup_fixture(obj)
        self.assertIs(tobiko.get_fixture(MY_FIXTURE_NAME), result)
        result.setup_fixture.assert_called_once_with()

    def test_cleanup_fixture_by_name(self):
        self._test_cleanup_fixture(MY_FIXTURE_NAME)

    def test_cleanup_fixture_by_type(self):
        self._test_cleanup_fixture(MyFixture)

    def _test_cleanup_fixture(self, obj):
        result = tobiko.cleanup_fixture(obj)
        self.assertIs(tobiko.get_fixture(MY_FIXTURE_NAME), result)
        result.cleanup_fixture.assert_called_once_with()

    def test_list_required_fixtures_from_module(self):
        result = tobiko.list_required_fixtures([__name__])
        self.assertEqual([MY_FIXTURE_NAME], result)

    def test_list_required_fixtures_from_testcase_type(self):
        result = tobiko.list_required_fixtures([FixtureManagerTest])
        self.assertEqual([MY_FIXTURE_NAME], result)

    def test_list_required_fixtures_from_fixture_type(self):
        result = tobiko.list_required_fixtures([MyFixture])
        self.assertEqual([MY_FIXTURE_NAME], result)

    def test_list_required_fixtures_from_fixture_name(self):
        result = tobiko.list_required_fixtures([MY_FIXTURE_NAME])
        self.assertEqual([MY_FIXTURE_NAME], result)

    def test_list_required_fixtures_from_method(
            self, fixture_type=MyFixture):
        result = tobiko.list_required_fixtures([self.id()])
        self.assertEqual([MY_FIXTURE_NAME], result)
        self.assertIsInstance(tobiko.get_fixture(MY_FIXTURE_NAME),
                              fixture_type)

    def test_list_required_fixtures_from_fixture_object(self):
        fixture = tobiko.get_fixture(MY_FIXTURE_NAME)
        result = tobiko.list_required_fixtures([fixture])
        self.assertEqual([MY_FIXTURE_NAME], result)


class SharedFixtureTest(unit.TobikoUnitTest):

    def test_init(self):
        fixture = MyFixture()
        fixture.setup_fixture.assert_not_called()
        fixture.cleanup_fixture.assert_not_called()

    def test_use_fixture(self):
        fixture = MyFixture()
        self.addCleanup(fixture.cleanup_fixture.assert_called_once_with)

        self.useFixture(fixture)
        fixture.setup_fixture.assert_called_once_with()
        fixture.cleanup_fixture.assert_not_called()

        self.useFixture(fixture)
        fixture.setup_fixture.assert_called_once_with()
        fixture.cleanup_fixture.assert_not_called()

    def test_add_cleanup(self):
        fixture = MyFixture()
        self.addCleanup(fixture.cleanup_fixture.assert_called_once_with)
        self.addCleanup(fixture.cleanUp)
        self.addCleanup(fixture.cleanUp)

    def test_setup(self):
        fixture = MyFixture()
        fixture.setUp()
        fixture.setup_fixture.assert_called_once_with()

    def test_setup_twice(self):
        fixture = MyFixture()
        fixture.setUp()
        fixture.setUp()
        fixture.setup_fixture.assert_called_once_with()

    def test_cleanup(self):
        fixture = MyFixture()
        fixture.cleanUp()
        fixture.cleanup_fixture.assert_called_once_with()

    def test_cleanup_twice(self):
        fixture = MyFixture()
        fixture.cleanUp()
        fixture.cleanup_fixture.assert_called_once_with()

    def test_lifecycle(self):
        fixture = MyFixture()

        for call_count in range(3):
            fixture.setUp()
            fixture.setup_fixture.assert_has_calls([mock.call()] * call_count)
            fixture.setUp()
            fixture.setup_fixture.assert_has_calls([mock.call()] * call_count)

            fixture.cleanUp()
            fixture.cleanup_fixture.assert_has_calls(
                [mock.call()] * call_count)
            fixture.cleanUp()
            fixture.cleanup_fixture.assert_has_calls(
                [mock.call()] * call_count)
