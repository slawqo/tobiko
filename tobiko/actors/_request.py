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
import typing


class ActorRequest(typing.NamedTuple):
    future: asyncio.Future
    actor_id: str
    method: str
    arguments: typing.Dict[str, typing.Any]


class ActorRequestQueue(abc.ABC):

    @abc.abstractmethod
    def send_request(self,
                     actor_id: str,
                     method: str,
                     arguments: typing.Dict[str, typing.Any]) \
            -> asyncio.Future:
        raise NotImplementedError

    async def cancel_requests(self,
                              actor_id: str = None) \
            -> typing.List[ActorRequest]:
        return await self.drain_requests(actor_id=actor_id,
                                         cancel=True)

    @abc.abstractmethod
    async def drain_requests(self,
                             actor_id: str = None,
                             cancel=False) -> typing.List[ActorRequest]:
        raise NotImplementedError

    @abc.abstractmethod
    async def receive_request(self) -> ActorRequest:
        raise NotImplementedError


class AsyncioActorRequestQueue(ActorRequestQueue):

    def __init__(self,
                 loop: asyncio.AbstractEventLoop,
                 max_size=0):
        self.max_size = max_size
        self._loop = loop
        self._queue: asyncio.Queue = self._init_queue()

    def _init_queue(self) -> asyncio.Queue:
        return asyncio.Queue(maxsize=self.max_size)

    def send_request(self,
                     actor_id: str,
                     method: str,
                     arguments: typing.Dict[str, typing.Any]) \
            -> asyncio.Future:
        future = self._loop.create_future()
        request = ActorRequest(future=future,
                               actor_id=actor_id,
                               method=method,
                               arguments=arguments)
        self._queue.put_nowait(request)
        return future

    async def drain_requests(self, actor_id: str = None,
                             cancel=False) \
            -> typing.List[ActorRequest]:
        old_queue = self._queue
        self._queue = self._init_queue()
        keep_requests = []
        drained_requests = []
        while True:
            try:
                request: ActorRequest = old_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if actor_id in [None, request.actor_id]:
                drained_requests.append(request)
                if cancel:
                    request.future.cancel()
            else:
                keep_requests.append(request)
        for request in keep_requests:
            await self._queue.put(request)
        return drained_requests

    async def receive_request(self) -> ActorRequest:
        return await self._queue.get()


def create_request_queue(loop: asyncio.AbstractEventLoop,
                         max_size=0) -> ActorRequestQueue:
    return AsyncioActorRequestQueue(loop=loop, max_size=max_size)
