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


import testtools

from tobiko.common import _exception


class TestCasesManager(object):

    def __init__(self):
        self._test_cases = []

    def get_test_case(self) -> testtools.TestCase:
        return self._test_cases[-1]

    def pop_test_case(self) -> testtools.TestCase:
        return self._test_cases.pop()

    def push_test_case(self, test_case: testtools.TestCase):
        _exception.check_valid_type(test_case, testtools.TestCase)
        self._test_cases.append(test_case)


TEST_CASES = TestCasesManager()


def push_test_case(test_case: testtools.TestCase, manager=TEST_CASES):
    return manager.push_test_case(test_case=test_case)


def pop_test_case(manager=TEST_CASES):
    return manager.pop_test_case()


def get_test_case(manager=TEST_CASES):
    return manager.get_test_case()


class TobikoTestCase(testtools.TestCase):

    def setUp(self):
        self._push_test_case()
        super(TobikoTestCase, self).setUp()

    def _push_test_case(self):
        push_test_case(self)
        self.addCleanup(self._pop_test_case)

    def _pop_test_case(self):
        self.assertIs(self, pop_test_case())
