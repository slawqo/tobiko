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
from unittest import mock

import tobiko
from tobiko.tests import unit


@tobiko.protocol
class MyProto:
    # pylint: disable=unused-argument

    def call_one(self, arg='a') -> int:
        return 42

    def call_two(self, *args) -> int:
        return 42

    def call_three(self, **kwargs) -> int:
        return 42


class MyProtoHandler(tobiko.CallHandler):

    protocol_class = MyProto


class ProxyTest(unit.TobikoUnitTest):

    def handle_call(self, method: typing.Callable, *_args, **_kwargs):
        self.assertTrue(inspect.isfunction(method))

    def mock_handler(self) -> typing.Callable:
        return typing.cast(typing.Callable,
                           mock.MagicMock(side_effect=self.handle_call))

    def test_call_handler(self):
        # pylint: disable=no-member
        handler = self.mock_handler()
        proxy: MyProto = MyProtoHandler(handler).use_as(MyProto)
        self.assertIsInstance(proxy, MyProto)
        self.assertTrue(callable(proxy.call_one))
        self.assertEqual(inspect.signature(MyProto.call_one),
                         inspect.signature(type(proxy).call_one))
        self.assertIsNot(MyProto.call_one,
                         proxy.call_one)
        proxy.call_one()
        handler.assert_called_with(MyProto.call_one, 'a')

    def test_call_proxy(self):
        handler = self.mock_handler()
        proxy = tobiko.call_proxy(MyProto, handler).use_as(MyProto)
        self.assertIsInstance(proxy, MyProto)
        self.assertTrue(callable(proxy.call_one))
        self.assertEqual(inspect.signature(MyProto.call_one),
                         inspect.signature(type(proxy).call_one))
        self.assertIsNot(MyProto.call_one,
                         proxy.call_one)
        proxy.call_one()
        handler.assert_called_with(MyProto.call_one, 'a')
        proxy.call_one('b')
        handler.assert_called_with(MyProto.call_one, 'b')
        proxy.call_one(arg='c')
        handler.assert_called_with(MyProto.call_one, 'c')

        proxy.call_two(1, 2, 3)
        handler.assert_called_with(MyProto.call_two, 1, 2, 3)

        proxy.call_three(a='a', b='b')
        handler.assert_called_with(MyProto.call_three, a='a', b='b')
