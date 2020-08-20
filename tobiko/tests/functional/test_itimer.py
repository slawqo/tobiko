# Copyright (c) 2020 Red Hat, Inc.
#
# All Rights Reserved.
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

import itertools
import signal
import time
import traceback

import testtools

import tobiko


class ITimerTest(testtools.TestCase):

    do_wait = True

    def test_itimer(self, signal_number=None, delay=0.01,
                    exception=tobiko.ITimerExpired, on_timeout=None):
        with tobiko.itimer(delay=delay, signal_number=signal_number,
                           on_timeout=on_timeout):
            if exception is None:
                self._wait_for_timeout()
            else:
                ex = self.assertRaises(exception, self._wait_for_timeout)
                self.assertEqual(signal_number or signal.SIGALRM,
                                 ex.signal_number)
                self.assertIn('_wait_for_timeout', ex.stack)

    def test_itimer_with_sigalrm(self):
        self.test_itimer(signal_number=signal.SIGALRM)

    def test_itimer_with_sigvtalrm(self):
        self.test_itimer(signal_number=signal.SIGVTALRM)

    def test_itimer_with_sigprof(self):
        self.test_itimer(signal_number=signal.SIGPROF)

    def test_itimer_with_on_timeout(self):

        counter = itertools.count()

        def on_timeout(signal_number, frame):
            self.do_wait = False
            next(counter)
            self.assertEqual(signal.SIGALRM, signal_number)
            stack = traceback.extract_stack(frame, 1)
            self.assertEqual('_wait_for_timeout', stack[0].name)

        self.test_itimer(signal_number=signal.SIGALRM,
                         on_timeout=on_timeout,
                         exception=None)
        self.assertEqual(1, next(counter))

    def _wait_for_timeout(self):
        while self.do_wait:
            time.sleep(0.)
