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

import tobiko
from tobiko.tests import unit


class TestCaseTest(unit.TobikoUnitTest):

    def setUp(self):
        super(TestCaseTest, self).setUp()
        self.addCleanup(self._pop_inner_test_cases)

    def _pop_inner_test_cases(self):
        case = tobiko.get_test_case()
        while case is not self:
            tobiko.pop_test_case()
            case = tobiko.get_test_case()

    def test_get_test_case(self):
        result = tobiko.get_test_case()
        self.assertIs(self, result)

    def test_get_test_case_out_of_context(self):
        manager = tobiko.TestCasesManager()
        result = tobiko.get_test_case(manager=manager)
        self.assertIsInstance(result, testtools.TestCase)
        self.assertEqual('tobiko.common._testcase.DummyTestCase.runTest',
                         result.id())

    def test_push_test_case(self):

        class InnerTest(testtools.TestCase):

            def runTest(self):
                pass

        inner_case = InnerTest()

        tobiko.push_test_case(inner_case)
        self.assertIs(inner_case, tobiko.get_test_case())

    def test_pop_test_case(self):

        class InnerTest(testtools.TestCase):

            def runTest(self):
                pass

        inner_case = InnerTest()
        tobiko.push_test_case(inner_case)

        result = tobiko.pop_test_case()

        self.assertIs(inner_case, result)
        self.assertIs(self, tobiko.get_test_case())
