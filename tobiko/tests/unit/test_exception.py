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

import sys

import tobiko
from tobiko.tests import unit


class SomeException(tobiko.TobikoException):
    message = "message formatted with {b} and {a}"


class TestException(unit.TobikoUnitTest):

    def test_init(self, message=None, **properties):
        ex = SomeException(message, **properties)
        expected_str = message or SomeException.message
        if properties:
            expected_str = expected_str.format(**properties)
        self.assertEqual(expected_str, str(ex))
        for k, v in properties.items():
            self.assertEqual(v, getattr(ex, k))

    def test_init_with_properties(self):
        self.test_init(a='a', b='b')

    def test_init_with_message(self):
        self.test_init('{other} message', other='another')

    def test_raise(self):
        def _raise_my_exception(**kwargs):
            raise SomeException(**kwargs)
        ex = self.assertRaises(SomeException, _raise_my_exception, b=1, a=2)
        self.assertEqual('message formatted with 1 and 2', str(ex))

    def test_repr(self):
        ex = SomeException('some reason')
        self.assertEqual("SomeException('some reason')", repr(ex))

    def test_get_invalid_property(self):
        ex = SomeException(a='1', b='2')

        def _get_invalid_property():
            return ex.invalid_attribute_name

        ex = self.assertRaises(AttributeError, _get_invalid_property)
        self.assertEqual(
            "SomeException('message formatted with 2 and 1') object has no "
            "attribute 'invalid_attribute_name'", str(ex))

    def test_docstring_example(self):

        class MyException(tobiko.TobikoException):
            message = "This exception occurred because of {reason}"

        try:
            raise MyException(reason="something went wrong")
        except MyException as ex:
            self.assertEqual(
                'This exception occurred because of something went wrong',
                str(ex))
            self.assertEqual('something went wrong', ex.reason)


class TestCheckValidType(unit.TobikoUnitTest):

    def test_check_valid_type_with_no_type(self):
        self._test_check_is_valid_type_when_invalid(object())

    def test_check_valid_type_with_one_type(self):
        self._test_check_is_valid_type_when_valid(object(), object)

    def test_check_valid_type_with_two_types(self):
        self._test_check_is_valid_type_when_valid(object(), bool, object)

    def test_check_valid_type_with_one_wrong_type(self):
        self._test_check_is_valid_type_when_invalid(object(), bool)

    def test_check_valid_type_with_two_wrong_types(self):
        self._test_check_is_valid_type_when_invalid(object(), bool, int)

    def _test_check_is_valid_type_when_valid(self, obj, *valid_types):
        result = tobiko.check_valid_type(obj, *valid_types)
        self.assertIs(obj, result)

    def _test_check_is_valid_type_when_invalid(self, obj, *valid_types):
        ex = self.assertRaises(TypeError, tobiko.check_valid_type, obj,
                               *valid_types)
        tyes_str = ', '.join([str(t) for t in valid_types])
        message = ("Object {!s} is not of a valid type ({!s})"
                   ).format(repr(obj), tyes_str)

        self.assertEqual(message, str(ex))


class TestExcInfo(unit.TobikoUnitTest):

    def test_exc_info(self):
        try:
            raise RuntimeError('some error')
        except RuntimeError:
            exc_info = tobiko.exc_info()
            exc_type, exc_value, traceback = sys.exc_info()

        self.assertEqual((exc_type, exc_value, traceback), exc_info)
        self.assertIs(RuntimeError, exc_info.type)
        self.assertIs(exc_value, exc_info.value)
        self.assertIs(traceback, exc_info.traceback)

        reraised = self.assertRaises(RuntimeError, exc_info.reraise)
        self.assertIs(exc_value, reraised)
