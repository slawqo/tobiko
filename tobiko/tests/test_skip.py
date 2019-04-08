# Copyright (c) 2019 Red Hat
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

import tobiko
from tobiko.tests import unit


def condition(value):
    return value


class PositiveSkipTest(unit.TobikoUnitTest):

    @tobiko.skip_if('condition value was true',
                    condition, True)
    def test_skip_if_condition_called_with_args(self):
        self.fail('Not skipped')

    @tobiko.skip_if('condition value was true',
                    condition, value=True)
    def test_skip_if_condition_called_with_kwargs(self):
        self.fail('Not skipped')

    @tobiko.skip_until('condition value was false',
                       condition, False)
    def test_skip_until_condition_called_with_args(self):
        self.fail('Not skipped')

    @tobiko.skip_until('condition value was false',
                       condition, value=False)
    def test_skip_until_condition_called_with_kwargs(self):
        self.fail('Not skipped')


class NegativeSkipTest(unit.TobikoUnitTest):

    test_method_called = False

    def setUp(self):
        super(NegativeSkipTest, self).setUp()
        self.addCleanup(self.assert_test_method_called)

    def assert_test_method_called(self):
        self.assertTrue(self.test_method_called)

    @tobiko.skip_if('condition value was false',
                    condition, False)
    def test_skip_if_condition_called_with_args(self):
        self.test_method_called = True

    @tobiko.skip_if('condition value was false',
                    condition, value=False)
    def test_skip_if_condition_called_with_kwargs(self):
        self.test_method_called = True

    @tobiko.skip_until('condition value was true',
                       condition, True)
    def test_skip_until_condition_called_with_args(self):
        self.test_method_called = True

    @tobiko.skip_until('condition value was true',
                       condition, value=True)
    def test_skip_until_condition_called_with_kwargs(self):
        self.test_method_called = True
