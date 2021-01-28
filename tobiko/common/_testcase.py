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

import os
import sys
import typing  # noqa

import testtools

from tobiko.common import _exception


os.environ.setdefault('PYTHON', sys.executable)


class TestCasesManager(object):

    def __init__(self):
        self._test_cases: typing.List[testtools.TestCase] = []

    def get_test_case(self) -> testtools.TestCase:
        try:
            return self._test_cases[-1]
        except IndexError:
            return DUMMY_TEST_CASE

    def pop_test_case(self) -> testtools.TestCase:
        return self._test_cases.pop()

    def push_test_case(self, test_case: testtools.TestCase):
        _exception.check_valid_type(test_case, testtools.TestCase)
        self._test_cases.append(test_case)


TEST_CASES = TestCasesManager()


def push_test_case(test_case: testtools.TestCase,
                   manager: TestCasesManager = TEST_CASES):
    return manager.push_test_case(test_case=test_case)


def pop_test_case(manager: TestCasesManager = TEST_CASES) -> \
        testtools.TestCase:
    return manager.pop_test_case()


def get_test_case(manager: TestCasesManager = TEST_CASES) -> \
        testtools.TestCase:
    return manager.get_test_case()


class DummyTestCase(testtools.TestCase):

    def runTest(self):
        pass


DUMMY_TEST_CASE = DummyTestCase()


def run_test(test_case: testtools.TestCase,
             test_result: testtools.TestResult = None) -> testtools.TestResult:
    test_result = test_result or testtools.TestResult()
    test_case.run(test_result)
    return test_result


def assert_in(needle, haystack, message: typing.Optional[str] = None,
              manager: TestCasesManager = TEST_CASES):
    get_test_case(manager=manager).assertIn(needle, haystack, message)


def get_skipped_test_cases(test_result: testtools.TestResult,
                           skip_reason: typing.Optional[str] = None):
    if skip_reason is not None:
        assert_in(skip_reason, test_result.skip_reasons)
        return test_result.skip_reasons[skip_reason]
    else:
        skipped_test_cases = list()
        for cases in test_result.skip_reasons.values():
            skipped_test_cases.extend(cases)
        return skipped_test_cases


def assert_test_case_was_skipped(test_case: testtools.TestCase,
                                 test_result: testtools.TestResult,
                                 skip_reason: str = None,
                                 manager: TestCasesManager = TEST_CASES):
    skipped_tests = get_skipped_test_cases(test_result=test_result,
                                           skip_reason=skip_reason)
    assert_in(test_case, skipped_tests, manager=manager)
