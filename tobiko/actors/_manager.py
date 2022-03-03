# Copyright 2022 Red Hat
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
import typing

import tobiko
from tobiko.actors import _actor


A = typing.TypeVar('A', bound=_actor.ActorBase)


class ActorManager(tobiko.SharedFixture, tobiko.FixtureManager):
    pass


def actor_manager(obj: ActorManager = None) -> ActorManager:
    if obj is None:
        return tobiko.get_fixture(ActorManager)
    return tobiko.check_valid_type(obj, ActorManager)


ActorType = typing.Union[A, typing.Type[A]]


def start_actor(obj: ActorType,
                fixture_id: typing.Optional[str] = None,
                manager: ActorManager = None) -> _actor.ActorRef[A]:
    return tobiko.setup_fixture(obj,
                                fixture_id=fixture_id,
                                manager=manager).ref


async def setup_actor(obj: ActorType,
                      fixture_id: typing.Optional[str] = None,
                      manager=None,
                      timeout: tobiko.Seconds = None) -> _actor.ActorRef[A]:
    actor = tobiko.setup_fixture(obj,
                                 fixture_id=fixture_id,
                                 manager=manager)
    await asyncio.wait_for(actor.setup_actor_future,
                           timeout=timeout)
    return actor.ref


async def stop_actor(obj: ActorType,
                     fixture_id: typing.Optional[str] = None,
                     manager=None) -> _actor.ActorRef[A]:
    return tobiko.cleanup_fixture(obj,
                                  fixture_id=fixture_id,
                                  manager=manager).ref


async def cleanup_actor(obj: ActorType,
                        fixture_id: typing.Optional[str] = None,
                        manager=None,
                        timeout: tobiko.Seconds = None) -> _actor.ActorRef[A]:
    actor = tobiko.cleanup_fixture(obj,
                                   fixture_id=fixture_id,
                                   manager=manager)
    await asyncio.wait_for(actor.cleanup_actor_future,
                           timeout=timeout)
    return actor.ref
