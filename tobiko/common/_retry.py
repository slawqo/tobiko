# Copyright 2019 Red Hat
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

import functools
import itertools
import sys
import typing

from oslo_log import log
import testtools

from tobiko.common import _asserts
from tobiko.common import _exception
from tobiko.common import _time


LOG = log.getLogger(__name__)


class RetryException(_exception.TobikoException):
    pass


class RetryLimitError(RetryException):
    message = ("Retry limit exceeded ({attempt.details})")


class RetryCountLimitError(RetryLimitError):
    message = ("Retry count limit exceeded ({attempt.details})")


class RetryTimeLimitError(RetryLimitError):
    message = ("Retry time limit exceeded ({attempt.details})")


class RetryAttempt(object):

    def __init__(self,
                 number: int,
                 start_time: float,
                 elapsed_time: float,
                 count: typing.Optional[int] = None,
                 timeout: _time.Seconds = None,
                 interval: _time.Seconds = None):
        self.number = number
        self.start_time = start_time
        self.elapsed_time = elapsed_time
        self.count = count
        self.timeout = _time.to_seconds(timeout)
        self.interval = _time.to_seconds(interval)

    def __eq__(self, other):
        return (other.number == self.number and
                other.start_time == self.start_time and
                other.elapsed_time == self.elapsed_time and
                other.count == self.count and
                other.timeout == self.timeout and
                other.interval == self.interval)

    def __hash__(self):
        raise NotImplementedError

    @property
    def count_left(self) -> typing.Optional[int]:
        if self.count is None:
            return None
        else:
            return max(0, self.count - self.number)

    def check_count_left(self) -> _time.Seconds:
        if self.count_left == 0:
            _exception.exc_info().reraise()
            raise RetryCountLimitError(attempt=self)
        return self.count_left

    @property
    def time_left(self) -> _time.Seconds:
        if self.timeout is None:
            return None
        else:
            return max(0., self.timeout - self.elapsed_time)

    def check_time_left(self) -> _time.Seconds:
        if self.time_left == 0.:
            _exception.exc_info().reraise()
            raise RetryTimeLimitError(attempt=self)
        return self.time_left

    def check_limits(self):
        self.check_count_left()
        self.check_time_left()

    @property
    def details(self) -> str:
        details = []
        details.append(f"number={self.number}")
        if self.count is not None:
            details.append(f"count={self.count}")
        details.append(f"elapsed_time={self.elapsed_time}")
        if self.timeout is not None:
            details.append(f"timeout={self.timeout}")
        if self.interval is not None:
            details.append(f"interval={self.interval}")
        return ', '.join(details)

    def __repr__(self):
        return f"retry_attempt({self.details})"


def retry_attempt(number: int,
                  start_time: float,
                  elapsed_time: float,
                  count: typing.Optional[int] = None,
                  timeout: _time.Seconds = None,
                  interval: _time.Seconds = None) -> RetryAttempt:
    return RetryAttempt(number=number,
                        count=count,
                        start_time=start_time,
                        elapsed_time=elapsed_time,
                        timeout=timeout, interval=interval)


class Retry(object):

    def __init__(self,
                 count: typing.Optional[int] = None,
                 timeout: _time.Seconds = None,
                 interval: _time.Seconds = None):
        self.count = count
        self.timeout = _time.to_seconds(timeout)
        self.interval = _time.to_seconds(interval)

    def __eq__(self, other):
        return (other.count == self.count and
                other.timeout == self.timeout and
                other.interval == self.interval)

    def __hash__(self):
        raise NotImplementedError

    def __iter__(self) -> typing.Iterator[RetryAttempt]:
        start_time = _time.time()
        elapsed_time = 0.
        for number in itertools.count(1):
            attempt = retry_attempt(number=number,
                                    count=self.count,
                                    start_time=start_time,
                                    elapsed_time=elapsed_time,
                                    timeout=self.timeout,
                                    interval=self.interval)

            yield attempt

            attempt.check_limits()

            elapsed_time = _time.time() - start_time
            interval = self.interval
            if interval is not None:
                sleep_time = attempt.number * interval - elapsed_time
                sleep_time = max(0., sleep_time)
                time_left = attempt.time_left
                if sleep_time > 0.:
                    if time_left is None or time_left > sleep_time:
                        LOG.debug(f"Wait for {sleep_time} seconds before "
                                  f"retrying... ({attempt.details})")
                        _time.sleep(sleep_time)
                        elapsed_time = _time.time() - start_time

    @property
    def details(self) -> str:
        details = []
        if self.count is not None:
            details.append(f"count={self.count}")
        if self.timeout is not None:
            details.append(f"timeout={self.timeout}")
        if self.interval is not None:
            details.append(f"interval={self.interval}")
        return ', '.join(details)

    def __repr__(self):
        return f"retry({self.details})"


def retry(other_retry: typing.Optional[Retry] = None,
          count: typing.Optional[int] = None,
          timeout: _time.Seconds = None,
          interval: _time.Seconds = None,
          default_count: typing.Optional[int] = None,
          default_timeout: _time.Seconds = None,
          default_interval: _time.Seconds = None) -> Retry:

    if other_retry is not None:
        # Apply default values from the other Retry object
        _exception.check_valid_type(other_retry, Retry)
        count = count or other_retry.count
        timeout = timeout or other_retry.timeout
        interval = interval or other_retry.interval

    # Apply default values
    count = count or default_count
    timeout = timeout or default_timeout
    interval = interval or default_interval

    return Retry(count=count, timeout=timeout, interval=interval)


def retry_on_exception(
        exception: Exception,
        *exceptions: Exception,
        other_retry: typing.Optional[Retry] = None,
        count: typing.Optional[int] = None,
        timeout: _time.Seconds = None,
        interval: _time.Seconds = None,
        default_count: typing.Optional[int] = None,
        default_timeout: _time.Seconds = None,
        default_interval: _time.Seconds = None,
        on_exception: typing.Optional[typing.Callable] = None) -> \
        typing.Callable[[typing.Callable], typing.Callable]:

    retry_object = retry(other_retry=other_retry,
                         count=count,
                         timeout=timeout,
                         interval=interval,
                         default_count=default_count,
                         default_timeout=default_timeout,
                         default_interval=default_interval)
    exceptions = (exception,) + exceptions

    def decorator(func):
        if typing.TYPE_CHECKING:
            # Don't neet to wrap the function when going to check argument
            # types
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # pylint: disable=catching-non-exception
            for attempt in retry_object:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    attempt.check_limits()
                    if on_exception is not None:
                        on_exception(attempt, *args, **kwargs)
        return wrapper

    return decorator


def retry_test_case(*exceptions: Exception,
                    count: typing.Optional[int] = None,
                    timeout: _time.Seconds = None,
                    interval: _time.Seconds = None) -> \
                    typing.Callable[[typing.Callable], typing.Callable]:
    """Re-run test case method in case it fails
    """
    exceptions = exceptions or (_asserts.FailureException,)
    return retry_on_exception(*exceptions,
                              count=count,
                              timeout=timeout,
                              interval=interval,
                              default_count=3,
                              on_exception=on_test_case_retry_exception)


def on_test_case_retry_exception(attempt: RetryAttempt,
                                 test_case: testtools.TestCase,
                                 *_args, **_kwargs):
    # pylint: disable=protected-access
    _exception.check_valid_type(test_case, testtools.TestCase)
    test_case._report_traceback(sys.exc_info(),
                                f"traceback[attempt={attempt.number}]")
    LOG.exception("Re-run test after failed attempt. "
                  f"(attempt={attempt.number}, test='{test_case.id()}')")
