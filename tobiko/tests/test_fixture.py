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
import mock

import tobiko
from tobiko.tests import unit


class MyFixture(fixtures.Fixture):
    pass


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
        setup = self.patch('fixtures.Fixture.setUp')

        result = tobiko.setup_fixture(obj)

        setup.assert_called_once_with()
        self.assertIs(tobiko.get_fixture(obj), result)

    def test_cleanup_fixture_by_name(self):
        self._test_cleanup_fixture(MY_FIXTURE_NAME)

    def test_cleanup_fixture_by_type(self):
        self._test_cleanup_fixture(MyFixture)

    def _test_cleanup_fixture(self, obj):
        cleanup = mock.MagicMock()
        fixture = tobiko.setup_fixture(obj)
        fixture.addCleanup(cleanup)

        result = tobiko.cleanup_fixture(obj)

        cleanup.assert_called_once_with()
        self.assertIs(tobiko.get_fixture(obj), result)

    def test_list_required_fixtures_from_module(self):
        result = tobiko.list_required_fixtures([__name__])
        self.assertEqual([MY_FIXTURE_NAME, MY_SHARED_FIXTURE_NAME], result)

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

    def test_setup_required_fixtures(self, fixture_type=MyFixture):
        setup = self.patch('fixtures.Fixture.setUp')

        result = list(tobiko.setup_required_fixtures([self.id()]))

        setup.assert_called_once_with()
        self.assertEqual([tobiko.get_fixture(fixture_type)], result)

    def test_cleanup_required_fixtures(self, fixture_type=MyFixture):
        cleanup = mock.MagicMock()
        fixture = tobiko.setup_fixture(fixture_type)
        fixture.addCleanup(cleanup)

        result = list(tobiko.cleanup_required_fixtures([self.id()]))

        cleanup.assert_called_once_with()
        self.assertEqual([tobiko.get_fixture(fixture_type)], result)


class MySharedFixture(tobiko.SharedFixture):
    pass


MY_SHARED_FIXTURE_NAME = __name__ + '.' + MySharedFixture.__name__


class SharedFixtureTest(unit.TobikoUnitTest):

    def setUp(self):
        super(SharedFixtureTest, self).setUp()
        tobiko.remove_fixture(MySharedFixture)
        self.mock_setup = self.patch('fixtures.Fixture.setUp')
        self.mock_cleanup = self.patch('fixtures.Fixture.cleanUp')

    def test_initial_state(self):
        self.mock_setup.assert_not_called()
        self.mock_cleanup.assert_not_called()

    def test_use_fixture(self):
        self.addCleanup(self.mock_cleanup.assert_not_called)
        fixture = tobiko.get_fixture(MySharedFixture)

        self.useFixture(fixture)
        self.mock_setup.assert_called_once_with()

        self.useFixture(fixture)
        self.mock_setup.assert_called_once_with()

    def test_setup_fixture(self):
        tobiko.setup_fixture(MySharedFixture)
        tobiko.setup_fixture(MySharedFixture)
        self.mock_setup.assert_called_once_with()

    def test_cleanup_fixture(self):
        tobiko.cleanup_fixture(MySharedFixture)
        self.mock_cleanup.assert_not_called()

    def test_setup_shared_fixture(self):
        tobiko.setup_shared_fixture(MySharedFixture)
        tobiko.setup_shared_fixture(MySharedFixture)
        self.mock_setup.assert_has_calls([mock.call(), mock.call()])

    def test_cleanup_shared_fixture(self):
        tobiko.cleanup_shared_fixture(MySharedFixture)
        self.mock_cleanup.assert_called_once()

    def test_cleanup_shared_fixture_workflow(self):
        tobiko.setup_fixture(MySharedFixture)
        tobiko.setup_fixture(MySharedFixture)
        self.mock_setup.assert_called_once_with()

        tobiko.cleanup_shared_fixture(MySharedFixture)
        self.mock_cleanup.assert_called_once()

        tobiko.setup_fixture(MySharedFixture)
        self.mock_setup.assert_has_calls([mock.call(), mock.call()])
