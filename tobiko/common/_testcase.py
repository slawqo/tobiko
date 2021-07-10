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
import typing

from oslo_log import log
import testtools

from tobiko.common import _exception
from tobiko.common import _time


LOG = log.getLogger(__name__)

os.environ.setdefault('PYTHON', sys.executable)


class TestCaseEntry(typing.NamedTuple):
    test_case: testtools.TestCase
    start_time: float


class TestCasesManager(object):

    start_time: _time.Seconds = None

    def __init__(self):
        self._test_cases: typing.List[TestCaseEntry] = []

    def get_test_case(self) -> testtools.TestCase:
        try:
            return self._test_cases[-1].test_case
        except IndexError:
            return DUMMY_TEST_CASE

    def pop_test_case(self) -> testtools.TestCase:
        entry = self._test_cases.pop()
        elapsed_time = _time.time() - entry.start_time
        LOG.debug(f"Exit test case '{entry.test_case.id()}' after "
                  f"{elapsed_time} seconds")
        return entry.test_case

    def push_test_case(self, test_case: testtools.TestCase):
        _exception.check_valid_type(test_case, testtools.TestCase)
        entry = TestCaseEntry(test_case=test_case,
                              start_time=_time.time())
        self._test_cases.append(entry)
        LOG.debug(f"Enter test case '{test_case.id()}'")


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
