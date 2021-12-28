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
import unittest

from oslo_log import log
import testtools

from tobiko.common import _exception
from tobiko.common import _time


LOG = log.getLogger(__name__)

os.environ.setdefault('PYTHON', sys.executable)

TestCase = unittest.TestCase


class TestCaseEntry(typing.NamedTuple):
    test_case: unittest.TestCase
    start_time: float


class TestCasesManager(object):

    start_time: _time.Seconds = None

    def __init__(self):
        self._test_cases: typing.List[TestCaseEntry] = []

    def get_test_case(self) -> unittest.TestCase:
        try:
            return self._test_cases[-1].test_case
        except IndexError:
            return DUMMY_TEST_CASE

    def pop_test_case(self) -> unittest.TestCase:
        entry = self._test_cases.pop()
        elapsed_time = _time.time() - entry.start_time
        LOG.debug(f"Exit test case '{entry.test_case.id()}' after "
                  f"{elapsed_time} seconds")
        return entry.test_case

    def push_test_case(self, test_case: unittest.TestCase):
        _exception.check_valid_type(test_case, unittest.TestCase)
        entry = TestCaseEntry(test_case=test_case,
                              start_time=_time.time())
        self._test_cases.append(entry)
        LOG.debug(f"Enter test case '{test_case.id()}'")


TEST_CASES = TestCasesManager()


def push_test_case(test_case: unittest.TestCase,
                   manager: TestCasesManager = TEST_CASES):
    return manager.push_test_case(test_case=test_case)


def pop_test_case(manager: TestCasesManager = TEST_CASES) -> \
        unittest.TestCase:
    return manager.pop_test_case()


def get_test_case(manager: TestCasesManager = TEST_CASES) -> \
        unittest.TestCase:
    return manager.get_test_case()


class DummyTestCase(unittest.TestCase):

    def runTest(self):
        pass


DUMMY_TEST_CASE = DummyTestCase()


def run_test(test_case: unittest.TestCase,
             test_result: unittest.TestResult = None,
             manager: TestCasesManager = TEST_CASES) -> unittest.TestResult:
    test_result = test_result or unittest.TestResult()
    push_test_case(test_case, manager=manager)
    try:
        test_case.run(test_result)
    finally:
        popped = pop_test_case(manager=manager)
        assert test_case is popped
    return test_result


def assert_in(needle, haystack, message: typing.Optional[str] = None,
              manager: TestCasesManager = TEST_CASES):
    get_test_case(manager=manager).assertIn(needle, haystack, message)


def get_skipped_test_cases(test_result: unittest.TestResult,
                           skip_reason: str = None) \
        -> typing.List[unittest.TestCase]:
    if isinstance(test_result, testtools.TestResult):
        raise NotImplementedError(
            f"Unsupported result type: {test_result}")
    return [case
            for case, reason in test_result.skipped
            if skip_reason is None or skip_reason in reason]


def assert_test_case_was_skipped(test_case: testtools.TestCase,
                                 test_result: testtools.TestResult,
                                 skip_reason: str = None,
                                 manager: TestCasesManager = TEST_CASES):
    skipped_tests = get_skipped_test_cases(test_result=test_result,
                                           skip_reason=skip_reason)
    assert_in(test_case, skipped_tests, manager=manager)


FailureException = typing.cast(
    typing.Tuple[Exception, ...],
    (unittest.TestCase.failureException,
     testtools.TestCase.failureException,
     AssertionError))


def fail(msg: str,
         cause: typing.Type[Exception] = None) -> typing.NoReturn:
    """Fail immediately current test case execution, with the given message.

    Unconditionally raises a tobiko.FailureException as in below equivalent
    code:

        raise FailureException(msg.format(*args, **kwargs))

    :param msg: string message used to create FailureException
    :param cause: error that caused the failure
    :returns: It never returns
    :raises failure_type or FailureException exception type:
    """
    failure_type = get_test_case().failureException
    raise failure_type(msg) from cause


def add_cleanup(function: typing.Callable, *args, **kwargs):
    get_test_case().addCleanup(function, *args, **kwargs)
