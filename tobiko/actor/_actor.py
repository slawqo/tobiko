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

import asyncio
import inspect
import logging
import typing

from oslo_log import log

import tobiko
from tobiko.actor import _request


T = typing.TypeVar('T')


class ActorRef(tobiko.CallHandler):

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


class Actor(tobiko.SharedFixture):
    max_queue_size: int = 0

    log: logging.LoggerAdapter
    loop: asyncio.AbstractEventLoop

    base_ref_class = ActorRef

    _actor_methods: typing.Dict[str, typing.Callable]
    _ref_class: type
    _ref: ActorRef
    _requests: _request.ActorRequestQueue
    _run_actor_task: asyncio.Task

    @property
    def actor_id(self) -> str:
        return self.fixture_name

    def setup_fixture(self):
        self.loop = self.get_loop()
        self.log = self.create_log()
        self._requests = self.create_request_queue()

        self._run_actor_task = self.loop.create_task(
            self._run_actor())

    @classmethod
    def ref_class(cls) -> type:
        try:
            return cls._ref_class
        except AttributeError:
            pass
        name = cls.__name__ + 'Ref'
        bases = cls.base_ref_class,
        namespace = {'__module__': cls.__module__,
                     'protocol_class': cls}
        return type(name, bases, namespace)

    @property
    def ref(self) -> ActorRef:
        try:
            return self._ref
        except AttributeError:
            pass
        ref_class = self.ref_class()
        self._ref = ref = ref_class(actor_id=self.actor_id,
                                    requests=self._requests)
        return ref

    def get_loop(self) -> asyncio.AbstractEventLoop:
        return asyncio.get_event_loop()

    @classmethod
    def _get_actor_methods(cls) -> typing.Dict[str, typing.Callable]:
        try:
            return cls._actor_methods
        except AttributeError:
            pass
        cls._actor_methods = dict(inspect.getmembers(cls, is_actor_method))
        return cls._actor_methods

    def create_log(self):
        return log.getLogger(self.actor_id)

    def create_request_queue(self) -> _request.ActorRequestQueue:
        return _request.create_request_queue(max_size=self.max_queue_size,
                                             loop=self.loop)

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
                    request = await self._requests.receive_request()
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
        methods = self._get_actor_methods()
        method = methods.get(name)
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


def create_actor(obj: typing.Union[str, Actor, typing.Type[Actor]],
                 fixture_id: typing.Optional[str] = None,
                 manager=None) -> ActorRef:
    actor = tobiko.setup_fixture(obj,
                                 fixture_id=fixture_id,
                                 manager=manager)
    return actor.ref
