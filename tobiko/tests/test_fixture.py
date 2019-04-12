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

import sys

import fixtures
import mock

import tobiko
from tobiko.tests import unit
from tobiko.common import _fixture


def canonical_name(cls):
    return __name__ + '.' + cls.__name__


class MyBaseFixture(tobiko.SharedFixture):

    def __init__(self):
        super(MyBaseFixture, self).__init__()
        self.setup_fixture = mock.Mock(
            specs=tobiko.SharedFixture.setup_fixture)
        self.cleanup_fixture = mock.Mock(
            specs=tobiko.SharedFixture.cleanup_fixture)


class MyFixture(MyBaseFixture):
    pass


class FixtureBaseTest(unit.TobikoUnitTest):

    def setUp(self):
        super(FixtureBaseTest, self).setUp()
        self.manager = _fixture.FixtureManager()
        self.patch_object(_fixture, 'FIXTURES', self.manager)


class GetFixtureTest(FixtureBaseTest):

    def test_by_name(self):
        self._test_get_fixture(canonical_name(MyFixture))

    def test_by_type(self):
        self._test_get_fixture(MyFixture)

    def _test_get_fixture(self, obj):
        fixture = tobiko.get_fixture(obj)
        self.assertIsInstance(fixture, MyFixture)
        self.assertIs(fixture, tobiko.get_fixture(obj))
        if isinstance(obj, fixtures.Fixture):
            self.assertIs(obj, fixture)
        else:
            self.assertIs(fixture, tobiko.get_fixture(
                canonical_name(MyFixture)))
        fixture.setup_fixture.assert_not_called()
        fixture.cleanup_fixture.assert_not_called()

    def test_by_instance(self):
        self._test_get_fixture(MyFixture())


class GetFixtureNameTest(FixtureBaseTest):

    def test_with_instance(self):
        fixture = MyFixture()
        result = tobiko.get_fixture_name(fixture)
        self.assertEqual(canonical_name(MyFixture), result)


class RemoveFixtureTest(FixtureBaseTest):

    def test_with_name(self):
        self._test_remove_fixture(canonical_name(MyFixture))

    def test_with_type(self):
        self._test_remove_fixture(MyFixture)

    def _test_remove_fixture(self, obj):
        fixture = tobiko.get_fixture(obj)
        result = tobiko.remove_fixture(obj)
        self.assertIs(fixture, result)
        self.assertIsNot(fixture, tobiko.get_fixture(obj))
        fixture.setup_fixture.assert_not_called()
        fixture.cleanup_fixture.assert_not_called()


class SetupFixtureTest(FixtureBaseTest):

    def test_with_name(self):
        self._test_setup_fixture(canonical_name(MyFixture))

    def test_with_type(self):
        self._test_setup_fixture(MyFixture)

    def test_with_instance(self):
        self._test_setup_fixture(MyFixture2())

    def _test_setup_fixture(self, obj):
        result = tobiko.setup_fixture(obj)
        self.assertIs(tobiko.get_fixture(obj), result)
        result.setup_fixture.assert_called_once_with()
        result.cleanup_fixture.assert_not_called()


class CleanupFixtureTest(FixtureBaseTest):

    def test_with_name(self):
        self._test_cleanup_fixture(canonical_name(MyFixture))

    def test_with_type(self):
        self._test_cleanup_fixture(MyFixture)

    def test_with_instance(self):
        self._test_cleanup_fixture(MyFixture())

    def _test_cleanup_fixture(self, obj):
        result = tobiko.cleanup_fixture(obj)
        self.assertIs(tobiko.get_fixture(obj), result)
        result.setup_fixture.assert_not_called()
        result.cleanup_fixture.assert_called_once_with()


class MyFixture2(MyBaseFixture):
    pass


class MyRequiredFixture(MyBaseFixture):
    pass


class MyRequiredSetupFixture(MyBaseFixture):
    pass


class ListRequiredFixtureTest(FixtureBaseTest):

    required_fixture = tobiko.required_fixture(MyRequiredFixture)
    required_setup_fixture = tobiko.required_setup_fixture(
        MyRequiredSetupFixture)

    def test_with_module(self):
        module = sys.modules[__name__]
        result = tobiko.list_required_fixtures([module])
        self.assertEqual([], result)

    def test_with_module_name(self):
        result = tobiko.list_required_fixtures([__name__])
        self.assertEqual([], result)

    def test_with_testcase_type(self):
        result = tobiko.list_required_fixtures([ListRequiredFixtureTest])
        self.assertEqual([canonical_name(MyRequiredFixture),
                          canonical_name(MyRequiredSetupFixture)], result)

    def test_with_testcase_name(self):
        result = tobiko.list_required_fixtures(
            [canonical_name(ListRequiredFixtureTest)])
        self.assertEqual([canonical_name(MyRequiredFixture),
                          canonical_name(MyRequiredSetupFixture)], result)

    def test_with_unbound_method(self, fixture=MyFixture, fixture2=MyFixture2):
        result = tobiko.list_required_fixtures(
            [ListRequiredFixtureTest.test_with_unbound_method])
        self.assertEqual([canonical_name(fixture),
                          canonical_name(fixture2),
                          canonical_name(MyRequiredFixture),
                          canonical_name(MyRequiredSetupFixture)], result)

    def test_with_bound_method(self, fixture=MyFixture, fixture2=MyFixture2):
        result = tobiko.list_required_fixtures([self.test_with_bound_method])
        self.assertEqual([canonical_name(fixture),
                          canonical_name(fixture2),
                          canonical_name(MyRequiredFixture),
                          canonical_name(MyRequiredSetupFixture)], result)

    def test_with_method_name(self, fixture=MyFixture, fixture2=MyFixture2):
        result = tobiko.list_required_fixtures([self.id()])
        self.assertEqual([canonical_name(fixture),
                          canonical_name(fixture2),
                          canonical_name(MyRequiredFixture),
                          canonical_name(MyRequiredSetupFixture)], result)

    def test_with_fixture_name(self):
        result = tobiko.list_required_fixtures([canonical_name(MyFixture)])
        self.assertEqual([canonical_name(MyFixture)], result)

    def test_with_fixture(self):
        result = tobiko.list_required_fixtures([MyFixture()])
        self.assertEqual([canonical_name(MyFixture)], result)

    def test_with_fixture_type(self):
        result = tobiko.list_required_fixtures([MyFixture])
        self.assertEqual([canonical_name(MyFixture)], result)

    def test_required_fixture_property(self):
        fixture = self.required_fixture
        self.assertIsInstance(fixture, MyRequiredFixture)
        fixture.setup_fixture.assert_not_called()
        fixture.cleanup_fixture.assert_not_called()

    def test_required_setup_fixture_property(self):
        fixture = self.required_setup_fixture
        self.assertIsInstance(fixture, MyRequiredSetupFixture)
        fixture.setup_fixture.assert_called_once_with()
        fixture.cleanup_fixture.assert_not_called()


class SharedFixtureTest(unit.TobikoUnitTest):

    def setUp(self):
        super(SharedFixtureTest, self).setUp()
        tobiko.remove_fixture(MyFixture)

    def test_init(self):
        fixture = MyFixture()
        fixture.setup_fixture.assert_not_called()
        fixture.cleanup_fixture.assert_not_called()

    def test_get(self):
        fixture = MyFixture.get()
        self.assertIs(tobiko.get_fixture(MyFixture), fixture)

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
