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

import abc
import functools
import inspect
import typing

import decorator


class ProtocolMeta(abc.ABCMeta):

    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        cls._is_protocol = True
        return cls


class Protocol(abc.ABC, metaclass=ProtocolMeta):
    pass


T = typing.TypeVar('T')


def is_protocol_class(cls):
    return cls.__dict__.get('_is_protocol', False)


def is_public_function(obj):
    return (inspect.isfunction(obj) and
            getattr(obj, '__name__', '_')[0] != '_')


class CallHandler(abc.ABC):

    def _handle_call(self, method: typing.Callable, *args, **kwargs):
        raise NotImplementedError


class CallProxy(CallHandler):

    _handle_call: typing.Callable

    def __init__(self, handle_call: typing.Callable):
        setattr(self, '_handle_call', handle_call)


@functools.lru_cache()
def call_proxy_class(protocol_class: type,
                     class_name: typing.Optional[str] = None,
                     handler_class: typing.Type[CallHandler] = CallProxy) \
        -> type:
    if not is_protocol_class(protocol_class):
        raise TypeError(f"{protocol_class} is not a subclass of {Protocol}")
    if class_name is None:
        class_name = protocol_class.__name__ + 'Proxy'
    namespace: typing.Dict[str, typing.Any] = {}
    for name, member in protocol_class.__dict__.items():
        if is_public_function(member):
            method = call_proxy_method(member)
            namespace[name] = method

    return type(class_name, (handler_class, protocol_class), namespace)


def call_proxy(protocol_class: typing.Type[T], handle_call: typing.Callable) \
        -> T:
    proxy_class = call_proxy_class(typing.cast(type, protocol_class))
    return proxy_class(handle_call)


@functools.lru_cache()
def stack_classes(name: str, cls: type, *classes) -> type:
    return type(name, (cls,) + classes, {})


@functools.lru_cache()
def list_protocols(cls: type) -> typing.Tuple[typing.Type[Protocol], ...]:
    subclasses = inspect.getmro(cls)
    protocols = tuple(typing.cast(typing.Type[Protocol], cls)
                      for cls in subclasses
                      if is_protocol_class(cls))
    return tuple(protocols)


def call_proxy_method(func: typing.Callable) -> typing.Callable:
    return decorator.decorate(func, _call_proxy_method)


def _call_proxy_method(func, self: CallHandler, *args, **kwargs):
    # pylint: disable=protected-access
    return self._handle_call(func, *args, **kwargs)
