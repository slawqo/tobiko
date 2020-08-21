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

import time

import testtools


class TestCaseTest(testtools.TestCase):

    def test_with_timeout(self):

        class MyTest(testtools.TestCase):

            _testcase_timeout = 1.

            def test_busy(self):
                while True:
                    time.sleep(0.)

        test_case = MyTest('test_busy')
        test_result = testtools.TestResult()
        test_case.run(test_result)

        reported_test_case, reported_error = test_result.errors[-1]
        self.assertIs(test_case, reported_test_case)
        self.assertIn('TestCaseTimeoutError', reported_error)
