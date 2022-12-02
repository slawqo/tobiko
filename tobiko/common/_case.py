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

import contextlib
import os
import sys
import typing
import types
import unittest

from oslo_log import log
import testtools

import tobiko
from tobiko.common import _exception
from tobiko.common import _retry
from tobiko.common import _time


LOG = log.getLogger(__name__)

os.environ.setdefault('PYTHON', sys.executable)

TestResult = unittest.TestResult
TestCase = unittest.TestCase
TestSuite = unittest.TestSuite


class BaseTestCase(unittest.TestCase):
    """Base test case class for tobiko test cases

    The reason this for exist is to have a way to override other tools base
    classes methods
    """

    _subtest: typing.Optional[unittest.TestCase] = None

    def run(self, result: TestResult = None) -> typing.Optional[TestResult]:
        with enter_test_case(self):
            return super().run(result)


class TestToolsTestCase(BaseTestCase, testtools.TestCase):
    pass


class TestCaseEntry(typing.NamedTuple):
    case: TestCase
    start_time: float


class DummyTestCase(BaseTestCase):

    def runTest(self):
        raise RuntimeError('Dummy test case')

    @contextlib.contextmanager
    def subTest(self, msg: typing.Any = ..., **params) \
            -> typing.Iterator[None]:
        yield


class TestCaseManager:

    def __init__(self,
                 start_time: _time.Seconds = None):
        self._cases: typing.List[TestCaseEntry] = []
        self.start_time = start_time

    def get_test_case(self) -> TestCase:
        try:
            return self._cases[-1].case
        except IndexError:
            return DummyTestCase()

    def get_parent_test_case(self) -> typing.Optional[TestCase]:
        try:
            return self._cases[-2].case
        except IndexError:
            return None

    def pop_test_case(self) -> TestCase:
        entry = self._cases.pop()
        elapsed_time = _time.time() - entry.start_time
        LOG.debug(f"Exit test case '{entry.case.id()}' after "
                  f"{elapsed_time} seconds")
        return entry.case

    def push_test_case(self, case: TestCase) -> TestCase:
        case = _exception.check_valid_type(case, TestCase)
        entry = TestCaseEntry(case=case,
                              start_time=_time.time())
        parent = self.get_test_case()
        self._cases.append(entry)
        LOG.debug(f"Enter test case '{case.id()}'")
        return parent


TEST_CASE_MANAGER = TestCaseManager()


def test_case_manager(manager: TestCaseManager = None) -> TestCaseManager:
    if manager is None:
        return TEST_CASE_MANAGER
    else:
        return tobiko.check_valid_type(manager, TestCaseManager)


def push_test_case(case: TestCase,
                   manager: TestCaseManager = None) -> TestCase:
    manager = test_case_manager(manager)
    return manager.push_test_case(case=case)


def pop_test_case(manager: TestCaseManager = None) -> TestCase:
    manager = test_case_manager(manager)
    return manager.pop_test_case()


def get_test_case(manager: TestCaseManager = None) -> TestCase:
    manager = test_case_manager(manager)
    return manager.get_test_case()


def get_parent_test_case(manager: TestCaseManager = None) \
        -> typing.Optional[TestCase]:
    manager = test_case_manager(manager)
    return manager.get_parent_test_case()


@contextlib.contextmanager
def enter_test_case(case: TestCase,
                    manager: TestCaseManager = None):
    manager = test_case_manager(manager)
    parent = manager.push_test_case(case)
    try:
        with parent.subTest(case.id()):
            yield
    finally:
        assert case is manager.pop_test_case()
        tobiko.remove_test_from_all_shared_resources(case.id())


def test_case(case: TestCase = None,
              manager: TestCaseManager = None) -> TestCase:
    if case is None:
        case = get_test_case(manager=manager)
    return _exception.check_valid_type(case, TestCase)


def get_sub_test_id(case: TestCase = None,
                    manager: TestCaseManager = None) -> str:
    # pylint: disable=protected-access
    case = test_case(case=case, manager=manager)
    if case._subtest is None:  # type: ignore
        return case.id()
    else:
        return case._subtest.id()  # type: ignore


def get_test_result(case: TestCase = None,
                    manager: TestCaseManager = None) \
        -> TestResult:
    case = test_case(case=case, manager=manager)
    outcome = getattr(case, '_outcome', None)
    result = getattr(outcome, 'result', None)
    if result is None:
        return TestResult()
    else:
        return result


def test_result(result: TestResult = None,
                case: TestCase = None,
                manager: TestCaseManager = None) \
        -> TestResult:
    if result is None:
        result = get_test_result(case=case, manager=manager)
    return tobiko.check_valid_type(result, TestResult)


RunTestType = typing.Union[TestCase, TestSuite]


def run_test(case: RunTestType,
             manager: TestCaseManager = None,
             result: TestResult = None,
             check=True) -> TestResult:
    if result is None:
        if check:
            parent = get_test_case(manager=manager)
            forward = get_test_result(case=parent)
            result = ForwardTestResult(forward=forward,
                                       parent=parent)
        else:
            result = TestResult()

    case.run(result=result)
    return result


ExcInfoType = typing.Union[
    typing.Tuple[typing.Type[BaseException],
                 BaseException,
                 types.TracebackType],
    typing.Tuple[None, None, None]]


class ForwardTestResult(TestResult):

    def __init__(self,
                 forward: TestResult,
                 parent: TestCase,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.forward = forward
        self.parent = parent

    def startTest(self, test: TestCase):
        super().startTest(test)
        if hasattr(self.forward, 'startTest'):
            self.forward.startTest(test)

    def stopTest(self, test: TestCase):
        super().stopTest(test)
        if hasattr(self.forward, 'stopTest'):
            self.forward.stopTest(test)

    def addError(self, test: TestCase, err: ExcInfoType):
        super().addError(test, err)
        if hasattr(self.forward, 'addError'):
            self.forward.addError(test, err)
            # self.forward.addError(self.parent, err)

    def addFailure(self, test: TestCase, err: ExcInfoType):
        super().addFailure(test, err)
        if hasattr(self.forward, 'addFailure'):
            self.forward.addFailure(test, err)
            # self.forward.addFailure(self.parent, err)

    def addSubTest(self,
                   test: TestCase,
                   subtest: TestCase,
                   err: typing.Optional[ExcInfoType]):
        super().addSubTest(test, subtest, err)
        if hasattr(self.forward, 'addSubTest'):
            self.forward.addSubTest(test, subtest, err)

    def addSuccess(self, test: TestCase):
        super().addSuccess(test)
        if hasattr(self.forward, 'addSuccess'):
            self.forward.addSuccess(test)

    def addSkip(self, test, reason: str):
        super().addSkip(test, reason)
        if hasattr(self.forward, 'addSkip'):
            self.forward.addSkip(test, reason)

    def addExpectedFailure(self, test: TestCase, err: ExcInfoType):
        super().addExpectedFailure(test, err)
        if hasattr(self.forward, 'addExpectedFailure'):
            self.forward.addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test: TestCase):
        super().addUnexpectedSuccess(test)
        if hasattr(self.forward, 'addUnexpectedSuccess'):
            self.forward.addUnexpectedSuccess(test)


def assert_in(needle, haystack,
              message: str = None):
    case = get_test_case()
    case.assertIn(needle, haystack, message)


def get_skipped_test_cases(skip_reason: str = None,
                           result: TestResult = None,
                           case: TestCase = None,
                           manager: TestCaseManager = None) \
        -> typing.List[TestCase]:
    result = test_result(result=result, case=case, manager=manager)
    return [case
            for case, reason in result.skipped
            if skip_reason is None or skip_reason in reason]


def assert_test_case_was_skipped(needle: TestCase,
                                 skip_reason: str = None,
                                 result: TestResult = None,
                                 case: TestCase = None,
                                 manager: TestCaseManager = None):
    skipped = get_skipped_test_cases(skip_reason=skip_reason,
                                     result=result,
                                     case=case,
                                     manager=manager)
    assert_in(needle, skipped)


FailureException = typing.cast(
    typing.Tuple[Exception, ...],
    (unittest.TestCase.failureException,
     testtools.TestCase.failureException,
     AssertionError))


def failure_exception_type(case: TestCase = None,
                           manager: TestCaseManager = None) \
        -> typing.Type[Exception]:
    case = test_case(case=case, manager=manager)
    assert issubclass(case.failureException, Exception)
    return case.failureException


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
    failure_type = failure_exception_type()
    raise failure_type(msg) from cause


def add_cleanup(function: typing.Callable, *args, **kwargs):
    get_test_case().addCleanup(function, *args, **kwargs)


def test_id(case: TestCase = None,
            manager: TestCaseManager = None) \
        -> str:
    return test_case(case=case, manager=manager).id()


def sub_test(msg: str = None, **kwargs):
    case = get_test_case()
    return case.subTest(msg, **kwargs)


def setup_tobiko_config(conf):
    # pylint: disable=unused-argument
    unittest.TestCase = BaseTestCase
    testtools.TestCase = TestToolsTestCase


def retry_test_case(*exceptions: Exception,
                    count: int = None,
                    timeout: _time.Seconds = None,
                    sleep_time: _time.Seconds = None,
                    interval: _time.Seconds = None) -> \
                    typing.Callable[[typing.Callable], typing.Callable]:
    """Re-run test case method in case it fails
    """
    if not exceptions:
        exceptions = FailureException
    return _retry.retry_on_exception(*exceptions,
                                     count=count,
                                     timeout=timeout,
                                     sleep_time=sleep_time,
                                     interval=interval,
                                     default_count=3,
                                     on_exception=on_test_case_retry_exception)


def on_test_case_retry_exception(attempt: _retry.RetryAttempt,
                                 case: testtools.TestCase,
                                 *_args, **_kwargs):
    if isinstance(case, testtools.TestCase):
        # pylint: disable=protected-access
        case._report_traceback(sys.exc_info(),
                               f"traceback[attempt={attempt.number}]")
    LOG.exception("Re-run test after failed attempt. "
                  f"(attempt={attempt.number}, test='{case.id()}')")
