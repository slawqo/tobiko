# Copyright (c) 2022 Red Hat, Inc.
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

import functools
import os
import typing
import unittest

import testtools

from tobiko import run


def nested_test_case(test_method: typing.Callable[[testtools.TestCase], None]):

    @functools.wraps(test_method)
    def wrapper(self: unittest.TestCase):
        nested_counter = int(os.environ.get('NESTED_TEST_CASE', 0))
        if not nested_counter:
            os.environ['NESTED_TEST_CASE'] = str(nested_counter + 1)
            try:
                test_method(self)
            finally:
                if nested_counter:
                    os.environ['NESTED_TEST_CASE'] = str(nested_counter)
                else:
                    os.environ.pop('NESTED_TEST_CASE')
    return wrapper


class RunTestsTest(unittest.TestCase):

    @nested_test_case
    def test_run_tests(self):
        result = run.run_tests(__file__)
        self.assertGreater(result.testsRun, 0)

    @nested_test_case
    def test_run_tests_with_dir(self):
        test_dir = os.path.dirname(__file__)
        result = run.run_tests(test_path=test_dir)
        self.assertGreater(result.testsRun, 0)
