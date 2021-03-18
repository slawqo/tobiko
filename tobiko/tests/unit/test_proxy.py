# Copyright 2021 Red Hat
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

import inspect
import typing

import mock

import tobiko
from tobiko.tests import unit


class MyProto1(tobiko.Protocol):
    # pylint: disable=unused-argument

    def call_one(self, arg='a') -> int:
        return 42

    def call_two(self, *args) -> int:
        return 42

    def call_three(self, **kwargs) -> int:
        return 42


class ProxyTest(unit.TobikoUnitTest):

    def test_call_proxy(self):

        def handle_call(method: typing.Callable, *_args, **_kwargs):
            self.assertTrue(inspect.isfunction(method))

        handler = mock.MagicMock(side_effect=handle_call)
        proxy = tobiko.call_proxy(MyProto1,
                                  typing.cast(typing.Callable, handler))
        self.assertIsInstance(proxy, MyProto1)
        self.assertTrue(callable(proxy.call_one))
        self.assertEqual(inspect.signature(MyProto1.call_one),
                         inspect.signature(type(proxy).call_one))
        self.assertIsNot(MyProto1.call_one,
                         proxy.call_one)
        proxy.call_one()
        handler.assert_called_with(MyProto1.call_one, 'a')
        proxy.call_one('b')
        handler.assert_called_with(MyProto1.call_one, 'b')
        proxy.call_one(arg='c')
        handler.assert_called_with(MyProto1.call_one, 'c')

        proxy.call_two(1, 2, 3)
        handler.assert_called_with(MyProto1.call_two, 1, 2, 3)

        proxy.call_three(a='a', b='b')
        handler.assert_called_with(MyProto1.call_three, a='a', b='b')
