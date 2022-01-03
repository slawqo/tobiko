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

import unittest
from unittest import mock

import tobiko
from tobiko.tests import unit


class TestCaseTest(unit.TobikoUnitTest):

    def setUp(self):
        super(TestCaseTest, self).setUp()
        self.addCleanup(self._pop_inner_test_cases)

    def _pop_inner_test_cases(self):
        case = tobiko.get_test_case()
        while case is not self:
            tobiko.pop_test_case()
            case = tobiko.get_test_case()

    def test_get_test_case(self):
        result = tobiko.get_test_case()
        self.assertIs(self, result)

    def test_get_test_case_out_of_context(self):
        manager = tobiko.TestCasesManager()
        result = tobiko.get_test_case(manager=manager)
        self.assertIsInstance(result, unittest.TestCase)
        self.assertEqual('tobiko.common._testcase.DummyTestCase.runTest',
                         result.id())

    def test_push_test_case(self):

        class InnerTest(unittest.TestCase):

            def runTest(self):
                pass

        inner_case = InnerTest()
        tobiko.push_test_case(inner_case)
        self.assertIs(inner_case, tobiko.get_test_case())

    def test_pop_test_case(self):

        class InnerTest(unittest.TestCase):

            def runTest(self):
                pass

        inner_case = InnerTest()
        tobiko.push_test_case(inner_case)

        result = tobiko.pop_test_case()

        self.assertIs(inner_case, result)
        self.assertIs(self, tobiko.get_test_case())

    def test_add_cleanup(self,
                         *args,
                         error: Exception = None,
                         failure: str = None,
                         **kwargs):

        mock_func = mock.Mock()

        class InnerTest(unittest.TestCase):
            def runTest(self):
                tobiko.add_cleanup(mock_func, *args, **kwargs)
                if error is not None:
                    raise error
                if failure is not None:
                    self.fail(failure)

        inner_case = InnerTest()

        mock_func.assert_not_called()
        result = tobiko.run_test(inner_case)
        self.assertEqual(1, result.testsRun)
        mock_func.assert_called_once_with(*args, **kwargs)

        if error is not None:
            self.assertEqual(1, len(result.errors))
            for _error in result.errors:
                self.assertIs(inner_case, _error[0])
                self.assertIn(str(error), _error[1])
        else:
            self.assertEqual([], result.errors)

        if failure is not None:
            self.assertEqual(1, len(result.failures))
            for _failure in result.failures:
                self.assertIs(inner_case, _failure[0])
                self.assertIn(failure, _failure[1])
        else:
            self.assertEqual([], result.failures)

    def test_add_cleanup_with_args(self):
        self.test_add_cleanup(1, 2, a='a', b='b')

    def test_add_cleanup_with_error(self):
        self.test_add_cleanup(error=RuntimeError('some error'))

    def test_add_cleanup_with_failure(self):
        self.test_add_cleanup(failure='some_failure')


class TestFail(unit.TobikoUnitTest):

    def test_fail(self, cause: Exception = None):
        ex = self.assertRaises(tobiko.FailureException, tobiko.fail,
                               'some_reason', cause=cause)
        self.assertEqual('some_reason', str(ex))
        self.assertIs(cause, ex.__cause__)

    def test_fail_with_cause(self):
        self.test_fail(cause=RuntimeError())
