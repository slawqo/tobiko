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

import typing  # noqa

import tobiko
from tobiko.tests import unit


class Operation(tobiko.Operation):
    executed = False

    def run_operation(self):
        self.executed = True


class OperationForDecorator(Operation):
    pass


class OperationTest(unit.TobikoUnitTest):

    operation = tobiko.runs_operation(Operation)
    expect_after_operations = set()  # type: typing.Set[str]
    expect_executed_operations = set()  # type: typing.Set[str]

    def expect_is_after(self, operation):
        name = tobiko.get_operation_name(operation)
        return name in self.expect_after_operations

    def expect_is_executed(self, operation):
        name = tobiko.get_operation_name(operation)
        return name in self.expect_executed_operations

    def test_operation_config(self):
        config = tobiko.operation_config()
        self.assertFalse(config.run_operations)
        self.assertEqual(set(), config.after_operations)

    def test_operation(self, operation=None):
        operation = operation or self.operation
        expect_is_after = self.expect_is_after(operation)
        self.assertIs(not expect_is_after, operation.is_before)
        self.assertIs(expect_is_after, operation.is_after)
        expect_is_executed = self.expect_is_executed(operation)
        self.assertIs(expect_is_executed, operation.executed)

    @tobiko.with_operation(OperationForDecorator)
    def test_with_operation(self):
        operation = tobiko.get_operation(OperationForDecorator)
        self.test_operation(operation)

    @tobiko.before_operation(OperationForDecorator)
    def test_before_operation(self):
        operation = tobiko.get_operation(OperationForDecorator)
        self.test_operation(operation)

    @tobiko.after_operation(OperationForDecorator)
    def test_after_operation(self):
        operation = tobiko.get_operation(OperationForDecorator)
        if self.expect_is_after(operation):
            self.test_operation(operation)
        else:
            self.fail('Test method not skipped')

    @operation.with_operation
    def test_with_operation_method(self):
        self.test_operation()

    @operation.before_operation
    def test_before_operation_method(self):
        self.test_operation()

    @operation.after_operation
    def test_after_operation_method(self):
        if self.expect_is_after(self.operation):
            self.test_operation()
        else:
            self.fail('Test method not skipped')


class DontRunOperationsTest(OperationTest):

    patch_environ = {
        'TOBIKO_RUN_OPERATIONS': 'false'
    }


class DoRunOperationsTest(OperationTest):

    patch_environ = {
        'TOBIKO_RUN_OPERATIONS': 'true'
    }

    expect_run_operations = True
    expect_after_operations = {
        tobiko.get_operation_name(Operation),
        tobiko.get_operation_name(OperationForDecorator)}
    expect_executed_operations = expect_after_operations

    def test_operation_config(self):
        config = tobiko.operation_config()
        self.assertTrue(config.run_operations)
        self.assertEqual(set(), config.after_operations)


class AfterOperationsTest(OperationTest):

    patch_environ = {
        'TOBIKO_AFTER_OPERATIONS': tobiko.get_fixture_name(Operation)
    }

    expect_after_operations = {tobiko.get_operation_name(Operation)}

    def test_operation_config(self):
        config = tobiko.operation_config()
        self.assertFalse(config.run_operations)
        self.assertEqual(self.expect_after_operations,
                         config.after_operations)


class RunOperationsMixinTest(tobiko.RunsOperations, unit.TobikoUnitTest):

    patch_environ = {
        'TOBIKO_RUN_OPERATIONS': 'true'
    }

    operation = tobiko.runs_operation(Operation)

    def test_operation(self):
        self.assertTrue(self.operation.is_after)
        self.assertTrue(self.operation.executed)
