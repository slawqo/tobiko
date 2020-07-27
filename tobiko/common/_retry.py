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

import collections
import functools
import itertools
import typing

from oslo_log import log

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


class RetryAttempt(
        collections.namedtuple('RetryAttempt', ['number', 'count',
                                                'start_time', 'elapsed_time',
                                                'timeout', 'interval'])):
    @property
    def count_left(self) -> typing.Optional[int]:
        if self.count is None:
            return None
        else:
            return max(0, self.count - self.number)

    def check_count_left(self) -> _time.Seconds:
        with _exception.exc_info():
            if self.count_left == 0:
                raise RetryCountLimitError(attempt=self)
        return self.count_left

    @property
    def time_left(self) -> _time.Seconds:
        if self.timeout is None:
            return None
        else:
            return max(0., self.timeout - self.elapsed_time)

    def check_time_left(self) -> _time.Seconds:
        with _exception.exc_info():
            if self.time_left == 0.:
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

    count: typing.Optional[int] = None
    timeout: _time.Seconds = None
    interval: _time.Seconds = None

    def __init__(self,
                 count: typing.Optional[int] = None,
                 timeout: _time.Seconds = None,
                 interval: _time.Seconds = None):
        if count:
            self.count = count
        self.timeout = _time.to_seconds(timeout)
        self.interval = _time.to_seconds(interval)

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


def retry(count: typing.Optional[int] = None,
          timeout: _time.Seconds = None,
          interval: _time.Seconds = None) -> Retry:
    return Retry(count=count,
                 timeout=timeout,
                 interval=interval)


def retry_on_exception(exception: Exception,
                       *exceptions: typing.Tuple[Exception],
                       count: typing.Optional[int] = None,
                       timeout: _time.Seconds = None,
                       interval: _time.Seconds = None):

    failures = (exception,) + exceptions

    def decorator(func):
        if typing.TYPE_CHECKING:
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # pylint: disable=catching-non-exception
            for attempt in retry(count=count,
                                 timeout=timeout,
                                 interval=interval):
                try:
                    return func(*args, **kwargs)
                except failures:
                    attempt.check_limits()
        return wrapper

    return decorator
