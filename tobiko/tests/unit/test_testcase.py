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
import subprocess

import testtools

import tobiko
from tobiko.tests import unit


class DiscoverTestCasesTest(unit.TobikoUnitTest):

    test_path = os.path.dirname(__file__)

    def setUp(self):
        super(DiscoverTestCasesTest, self).setUp()

        top_dir = os.path.abspath(self.test_path)
        while os.path.isdir(top_dir) and top_dir != os.path.sep:
            if os.path.isfile(os.path.join(top_dir, 'tox.ini')):
                break
            top_dir = os.path.dirname(top_dir)
        else:
            self.fail("'tox.ini' file not found in any parent "
                      f"of directory '{self.test_path}'")

        if not os.path.isdir(os.path.join(top_dir, '.stestr')):
            subprocess.run(['stestr', 'init'], cwd=top_dir, check=True)
        self.top_dir = top_dir
        self.repo_url = top_dir

        # Move to top directory
        original_work_dir = os.getcwd()
        os.chdir(self.top_dir)
        self.addCleanup(os.chdir, original_work_dir)

    def test_discover_testcases(self):
        testcases = tobiko.discover_test_cases(test_path=self.test_path,
                                               top_dir=self.top_dir,
                                               repo_url=self.repo_url,
                                               filters=[self.id()])
        self.assertIn(self.id(), testcases)


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
        self.assertIsInstance(result, tobiko.BaseTestCase)
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
