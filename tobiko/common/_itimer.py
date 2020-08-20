# Copyright 2020 Red Hat
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

import signal
import traceback
import typing  # noqa

from tobiko.common import _exception
from tobiko.common import _fixture
from tobiko.common import _time


ITIMER_SIGNALS = {
    signal.SIGALRM: signal.ITIMER_REAL,
    signal.SIGVTALRM: signal.ITIMER_VIRTUAL,
    signal.SIGPROF: signal.ITIMER_PROF
}


class ITimerExpired(_exception.TobikoException):
    message = ("ITimer expired (signal_number={signal_number}):\n"
               "{stack}")


ITimerHandler = typing.Callable[[int, typing.Any], typing.Any]


class ITimer(_fixture.SharedFixture):

    signal_number: int = signal.SIGALRM
    delay: float = 0.
    interval: float = 0.

    original_delay: _time.Seconds = None
    original_interval: _time.Seconds = None
    original_handler: typing.Union[typing.Callable, int, None] = None

    def __init__(self,
                 signal_number: typing.Optional[int] = None,
                 delay: _time.Seconds = None,
                 interval: _time.Seconds = None,
                 on_timeout: typing.Optional[ITimerHandler] = None):
        super(ITimer, self).__init__()
        if signal_number is not None:
            self.signal_number = signal_number
        if delay is not None:
            self.delay = delay
        if interval is not None:
            self.interval = interval
        if on_timeout:
            setattr(self, 'on_timeout', on_timeout)

    def setup_fixture(self):
        self.setup_handler()
        self.setup_timer()

    def setup_handler(self):
        self.original_handler = signal.getsignal(self.signal_number)
        signal.signal(self.signal_number, self.on_timeout)
        self.addCleanup(self.cleanup_handler)

    def cleanup_handler(self):
        if self.original_handler is not None:
            signal.signal(self.signal_number, self.original_handler)
            del self.original_handler

    def setup_timer(self):
        self.original_delay, self.original_interval = signal.setitimer(
            self.which, self.delay, self.interval)
        self.addCleanup(self.cleanup_timer)

    def cleanup_timer(self):
        if (self.original_delay is not None and
                self.original_interval is not None):
            signal.setitimer(self.which, self.original_delay,
                             self.original_interval)
            del self.original_delay
            del self.original_interval

    @property
    def which(self):
        return ITIMER_SIGNALS[self.signal_number]

    def on_timeout(self, signal_number: int, frame: typing.Any):
        assert self.signal_number == signal_number
        stack = ''.join(traceback.format_stack(frame))
        raise ITimerExpired(signal_number=signal_number, stack=stack)


def itimer(signal_number: typing.Optional[int] = None,
           delay: _time.Seconds = None,
           interval: _time.Seconds = None,
           on_timeout: typing.Optional[ITimerHandler] = None):
    return ITimer(signal_number=signal_number,
                  delay=delay,
                  interval=interval,
                  on_timeout=on_timeout)
