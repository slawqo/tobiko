# Copyright (c) 2021 Red Hat, Inc.
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

import abc
import asyncio
import inspect
import logging
import typing

from oslo_log import log

import tobiko
from tobiko.actors import _proxy
from tobiko.actors import _request


P = typing.TypeVar('P', bound=abc.ABC)


class ActorRef(_proxy.CallProxyBase, typing.Generic[P]):

    def __init__(self, actor_id: str, requests: _request.ActorRequestQueue):
        super().__init__()
        self.actor_id = actor_id
        self._requests = requests

    def send_request(self, method: str, **arguments):
        return self._requests.send_request(method=method, arguments=arguments)

    def _handle_call(self, method: typing.Callable, *args, **kwargs) -> None:
        arguments = inspect.signature(method).bind(
            None, *args, **kwargs).arguments
        arguments.pop('self', None)
        return self.send_request(method.__name__, **arguments)


def is_actor_method(obj):
    return getattr(obj, '__tobiko_actor_method__', False)


def actor_method(obj):
    if not callable(obj):
        raise TypeError(f"Actor method {obj} is not callable")

    if not inspect.iscoroutinefunction(obj):
        raise TypeError(f"Actor method {obj} is not async")

    name = getattr(obj, '__name__', None)
    if name is None or hasattr(ActorRef, name) or hasattr(Actor, name):
        raise TypeError(f"Invalid method name: '{name}'")

    obj.__tobiko_actor_method__ = True
    return obj


class _DummyActorProtocol(abc.ABC):
    pass


class Actor(tobiko.SharedFixture, typing.Generic[P],
            metaclass=_proxy.GenericMeta):
    max_queue_size: int = 0

    log: logging.LoggerAdapter
    event_loop: asyncio.AbstractEventLoop
    actor_ref: P

    _actor_protocol = _DummyActorProtocol
    _actor_request_queue: _request.ActorRequestQueue
    _run_actor_task: asyncio.Task

    def __init_subclass__(cls,
                          *args,
                          **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._actor_methods = dict(inspect.getmembers(cls, is_actor_method))
        cls._actor_ref_class = ActorRef[cls._actor_protocol]

    def __class_getitem__(cls, item: typing.Type[P]):
        tobiko.check_valid_type(item, type)
        return type(cls.__name__, (cls, item), dict(_actor_protocol=item))

    @property
    def actor_id(self) -> str:
        return self.fixture_name

    def setup_fixture(self):
        self.log = self._setup_log()
        self.event_loop = self._setup_event_loop()
        self._actor_request_queue = self._setup_actor_request_queue()
        self.actor_ref = self._setup_actor_ref()
        self._run_actor_task = self.event_loop.create_task(
            self._run_actor())

    def _setup_log(self):
        return log.getLogger(self.actor_id)

    @staticmethod
    def _setup_event_loop() -> asyncio.AbstractEventLoop:
        return asyncio.get_event_loop()

    def _setup_actor_request_queue(self) -> _request.ActorRequestQueue:
        return _request.create_request_queue(max_size=self.max_queue_size,
                                             loop=self.event_loop)

    def _setup_actor_ref(self) -> P:
        return self._actor_ref_class(actor_id=self.actor_id,
                                     requests=self._actor_request_queue)

    async def setup_actor(self):
        pass

    async def cleanup_actor(self):
        pass

    async def on_setup_error(self):
        self.log.exception("Actor setup error")

    async def on_request_error(
            self, request: typing.Optional[_request.ActorRequest]):
        self.log.exception(f"Actor request error: {request}")

    async def on_cleanup_error(self):
        self.log.exception("Actor cleanup error")

    async def _run_actor(self):
        try:
            await self.setup_actor()
        except Exception:
            await self.on_setup_error()
            await self._cleanup_actor()
        else:
            while True:
                request = None
                try:
                    request = await (
                        self._actor_request_queue.receive_request())
                    if not isinstance(request, _request.ActorRequest):
                        raise TypeError(
                            f"Invalid actor request type: {request}")
                    await self._receive_request(request)
                except Exception:
                    await self.on_request_error(request=request)

    async def _cleanup_actor(self):
        try:
            await self.cleanup_actor()
        except Exception:
            await self.on_cleanup_error()

    def _get_actor_method(self, name: str) -> typing.Callable:
        method = self._actor_methods.get(name)
        if method is None:
            raise ValueError(f"Invalid request method name: {name}")
        return method

    async def _receive_request(self, request: _request.ActorRequest):
        method = self._get_actor_method(request.method)
        try:
            result = await method(self, **request.arguments)
        except Exception as ex:
            request.future.set_exception(ex)
        else:
            request.future.set_result(result)


def create_actor(obj: typing.Type[P],
                 fixture_id: typing.Optional[str] = None,
                 manager=None) -> P:
    actor = tobiko.setup_fixture(obj,
                                 fixture_id=fixture_id,
                                 manager=manager)
    return actor.actor_ref
