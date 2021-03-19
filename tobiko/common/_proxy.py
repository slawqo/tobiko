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

import functools
import inspect
import typing

import decorator


def protocol(cls: type) -> type:
    name = cls.__name__
    bases = inspect.getmro(cls)[1:]
    namespace = dict(cls.__dict__,
                     _is_protocol=True,
                     __module__=cls.__module__)
    return type(name, bases, namespace)


def is_protocol_class(cls):
    return inspect.isclass(cls) and cls.__dict__.get('_is_protocol', False)


def is_public_function(obj):
    return (inspect.isfunction(obj) and
            getattr(obj, '__name__', '_')[0] != '_')


T = typing.TypeVar('T')


class CallHandlerMeta(type):

    def __new__(mcls, name, bases, namespace, **kwargs):
        protocol_class = namespace.get('protocol_class')
        if protocol_class is not None:
            proxy_class = call_proxy_class(protocol_class)
            bases += proxy_class,
        return super().__new__(mcls, name, bases, namespace, **kwargs)


class CallHandler(metaclass=CallHandlerMeta):

    protocol_class: type

    def __init__(self,
                 handle_call: typing.Optional[typing.Callable] = None):
        if handle_call is not None:
            assert callable(handle_call)
            setattr(self, '_handle_call', handle_call)

    def _handle_call(self, method: typing.Callable, *args, **kwargs):
        pass

    def use_as(self, cls: typing.Type[T]) -> T:
        assert isinstance(self, cls)
        return typing.cast(T, self)


def call_proxy_class(
        cls: type,
        *bases: type,
        class_name: typing.Optional[str] = None,
        namespace: typing.Optional[dict] = None) \
        -> type:
    if not inspect.isclass(cls):
        raise TypeError(f"Object {cls} is not a class")
    if class_name is None:
        class_name = cls.__name__ + 'Proxy'
    protocol_classes = list_protocols(cls)
    if not protocol_classes:
        raise TypeError(f"Class {cls} doesn't implement any protocol")
    if namespace is None:
        namespace = {}
    for protocol_class in reversed(protocol_classes):
        for name, member in protocol_class.__dict__.items():
            if is_public_function(member):
                method = call_proxy_method(member)
                namespace[name] = method
    # Skip empty protocols
    if not namespace:
        raise TypeError(f"Class {cls} has any protocol specification")
    namespace['__module__'] = cls.__module__
    proxy_class = type(class_name, bases + protocol_classes, namespace)
    assert not is_protocol_class(proxy_class)
    assert not is_protocol_class(proxy_class)
    return proxy_class


def call_proxy(cls: type, handle_call: typing.Callable) -> CallHandler:
    proxy_class = call_proxy_class(cls, CallHandler)
    return proxy_class(handle_call)


@functools.lru_cache()
def list_protocols(cls: type) -> typing.Tuple[type, ...]:
    subclasses = inspect.getmro(cls)
    protocols = tuple(cls
                      for cls in subclasses
                      if is_protocol_class(cls))
    return tuple(protocols)


def call_proxy_method(func: typing.Callable) -> typing.Callable:
    method = decorator.decorate(func, _call_proxy_method)
    assert method is not func
    return method


def _call_proxy_method(func, self: CallHandler, *args, **kwargs):
    # pylint: disable=protected-access
    return self._handle_call(func, *args, **kwargs)
