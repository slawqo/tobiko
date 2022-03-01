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
import uuid

from oslo_log import log

import tobiko
from tobiko.actors import _proxy
from tobiko.actors import _request


P = typing.TypeVar('P', bound=abc.ABC)


class ActorRef(_proxy.CallProxyBase, typing.Generic[P], abc.ABC):

    def __init__(self, actor_id: str,
                 requests: _request.ActorRequestQueue):
        super().__init__()
        self.actor_id = actor_id
        self._requests = requests

    def send_request(self, method: str, **arguments):
        return self._requests.send_request(actor_id=self.actor_id,
                                           method=method,
                                           arguments=arguments)

    def _handle_call(self, method: typing.Callable, *args, **kwargs) \
            -> asyncio.Future:
        arguments = inspect.signature(method).bind(
            None, *args, **kwargs).arguments
        arguments.pop('self', None)
        return self.send_request(method.__name__, **arguments)

    def ping_actor(self, data: typing.Any = None) -> typing.Any:
        return self.send_request(method='ping_actor', data=data)


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

    _actor_protocol = _DummyActorProtocol
    _cancel_actor = False
    _run_actor_task: asyncio.Task

    # Class methods ----------------------------------------------------------

    def __init_subclass__(cls,
                          *args,
                          **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._actor_methods = dict(inspect.getmembers(cls, is_actor_method))
        cls._actor_ref_class: typing.Type[ActorRef[P]] = (
            ActorRef[cls._actor_protocol])

    def __class_getitem__(cls, item: typing.Type[P]):
        if isinstance(item, type):
            return type(cls.__name__, (cls, item), dict(_actor_protocol=item))
        else:
            return cls

    # Public instance methods ------------------------------------------------

    def __init__(self,
                 actor_id: str = None,
                 event_loop: asyncio.AbstractEventLoop = None,
                 log: logging.LoggerAdapter = None,
                 requests: _request.ActorRequestQueue = None,
                 ref: ActorRef[P] = None):
        # pylint: disable=redefined-outer-name
        super().__init__()
        if actor_id is None:
            actor_id = self._init_actor_id()
        self.actor_id = actor_id

        if event_loop is None:
            event_loop = self._init_event_loop()
        self.event_loop = event_loop

        if log is None:
            log = self._init_log()
        self.log = log

        if requests is None:
            requests = self._init_actor_request_queue()
        self.requests = requests

        if ref is None:
            ref = self._init_actor_ref()
        self.ref = typing.cast(P, ref)
        self.setup_future = event_loop.create_future()
        self.cleanup_future = event_loop.create_future()

    @property
    def actor_name(self) -> str:
        return tobiko.get_fixture_name(self)

    def setup_fixture(self):
        self.setup_future.cancel()
        self.setup_future = self.event_loop.create_future()
        self._run_actor_task = self.event_loop.create_task(
            self._run_actor())

    def cleanup_fixture(self):
        self.cleanup_future.cancel()
        self.cleanup_future = self.event_loop.create_future()
        self._cancel_actor = True
        self.ref.ping_actor('cleanup')  # must weak up the actor with a message

    async def setup_actor(self):
        pass

    async def cleanup_actor(self):
        pass

    async def on_request_error(
            self, request: typing.Optional[_request.ActorRequest]):
        pass

    async def on_cleanup_error(self):
        pass

    async def ping_actor(self, data: typing.Any = None) -> typing.Any:
        return data
    ping_actor.__tobiko_actor_method__ = True  # type: ignore[attr-defined]

    # Private instance methods -----------------------------------------------
    @staticmethod
    def _init_actor_id() -> str:
        return str(uuid.uuid4())

    def _init_log(self):
        return log.getLogger(self.actor_name)

    @staticmethod
    def _init_event_loop() -> asyncio.AbstractEventLoop:
        return asyncio.get_event_loop()

    def _init_actor_request_queue(self) -> _request.ActorRequestQueue:
        return _request.create_request_queue(max_size=self.max_queue_size,
                                             loop=self.event_loop)

    def _init_actor_ref(self) -> ActorRef[P]:
        return self._actor_ref_class(actor_id=self.actor_id,
                                     requests=self.requests)

    async def _run_actor(self):
        try:
            await self._setup_actor()
            self._cancel_actor = False
            while not self._cancel_actor:
                request = None
                try:
                    request = await self.requests.receive_request()
                    await self._receive_request(request)
                except Exception:
                    await self.on_request_error(request=request)
        finally:
            with tobiko.exc_info(reraise=True):
                await self._cleanup_actor()

    async def _setup_actor(self):
        try:
            self.log.debug(f'Actor setup started {self.actor_name}')
            await self.setup_actor()
        except Exception as ex:
            self.log.exception(
                f'Failed Setting up actor: {self.actor_name} '
                f'({self.actor_id})')
            self.setup_future.set_exception(ex)
        else:
            self.setup_future.set_result(self.ref)
            self.log.debug(f'Actor setup succeeded: {self.actor_name} '
                           f'({self.actor_id}).')

    async def _cleanup_actor(self):
        try:
            self.log.debug(f'Actor cleanup started: {self.actor_name} '
                           f'({self.actor_id}).')
            await self.cleanup_actor()
        except Exception as ex:
            self.cleanup_future.set_exception(ex)
            self.log.exception(
                f'Actor cleanup failed: {self.actor_name} '
                f'({self.actor_id}).')
        else:
            self.cleanup_future.set_result(self.ref)
            self.log.debug(f'Actor cleanup succeeded: {self.actor_name} '
                           f'({self.actor_id}).')
        finally:
            with tobiko.exc_info(reraise=True):
                await self.requests.cancel_requests(actor_id=self.actor_id)

    async def _receive_request(self, request: _request.ActorRequest):
        tobiko.check_valid_type(request, _request.ActorRequest)
        if request.actor_id != self.actor_id:
            raise ValueError(f"Invalid request actor_id: {request.actor_id}")
        method = self._get_actor_method(request.method)
        try:
            result = await method(self, **request.arguments)
        except Exception as ex:
            request.future.set_exception(ex)
        else:
            request.future.set_result(result)

    def _get_actor_method(self, name: str) -> typing.Callable:
        method = self._actor_methods.get(name)
        if method is None:
            raise ValueError(f"Invalid request method name: {name}")
        return method


ActorType = typing.Union[Actor[P], typing.Type[Actor[P]]]


def start_actor(obj: ActorType,
                fixture_id: typing.Optional[str] = None,
                manager=None) -> ActorRef[P]:
    return tobiko.setup_fixture(obj,
                                fixture_id=fixture_id,
                                manager=manager).ref


async def setup_actor(obj: ActorType,
                      fixture_id: typing.Optional[str] = None,
                      manager=None,
                      timeout: tobiko.Seconds = None) -> ActorRef[P]:
    actor = tobiko.setup_fixture(obj,
                                 fixture_id=fixture_id,
                                 manager=manager)
    await asyncio.wait_for(actor.setup_future,
                           timeout=timeout)
    return actor.ref


async def stop_actor(obj: ActorType,
                     fixture_id: typing.Optional[str] = None,
                     manager=None) -> ActorRef[P]:
    return tobiko.cleanup_fixture(obj,
                                  fixture_id=fixture_id,
                                  manager=manager).ref


async def cleanup_actor(obj: ActorType,
                        fixture_id: typing.Optional[str] = None,
                        manager=None,
                        timeout: tobiko.Seconds = None) -> ActorRef[P]:
    actor = tobiko.cleanup_fixture(obj,
                                   fixture_id=fixture_id,
                                   manager=manager)
    await asyncio.wait_for(actor.cleanup_future,
                           timeout=timeout)
    return actor.ref
