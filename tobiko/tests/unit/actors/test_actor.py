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
import typing

from tobiko.tests import unit
from tobiko import actors


class Greeter(abc.ABC):

    @abc.abstractmethod
    async def greet(self, whom: str, greeted: 'Greeted'):
        raise NotImplementedError


class Greeted:

    greeter: typing.Optional[Greeter] = None
    whom: typing.Optional[str] = None

    async def greeted(self, whom: str, greeter: Greeter):
        self.greeter = greeter
        self.whom = whom


class GreeterActor(actors.Actor[Greeter]):

    setup_called = False
    cleanup_called = False

    async def setup_actor(self):
        self.setup_called = True

    async def cleanup_actor(self):
        self.cleanup_called = True

    @actors.actor_method
    async def greet(self, whom: str, greeted: Greeted):
        assert isinstance(self, Greeter)
        assert isinstance(self, GreeterActor)
        assert self.setup_called
        assert not self.cleanup_called
        if not whom:
            raise ValueError("'whom' parameter can't be empty")

        self.log.info(f"Hello {whom}!")
        await greeted.greeted(whom=whom, greeter=self.actor_ref)


class ActorTest(unit.TobikoUnitTest):

    async def test_async_request(self):
        greeter = actors.create_actor(GreeterActor)
        self.assertIsInstance(greeter, actors.ActorRef)
        self.assertIsInstance(greeter, Greeter)
        greeted = Greeted()
        await greeter.greet(whom=self.id(), greeted=greeted)
        self.assertEqual(self.id(), greeted.whom)
        self.assertIs(greeter, greeted.greeter)

    async def test_async_request_failure(self):
        greeter = actors.create_actor(GreeterActor)
        self.assertIsInstance(greeter, actors.ActorRef)
        self.assertIsInstance(greeter, Greeter)
        greeted = Greeted()

        try:
            await greeter.greet(whom="", greeted=greeted)
        except ValueError as ex:
            self.assertEqual("'whom' parameter can't be empty", str(ex))
        else:
            self.fail("Exception not raised")
        self.assertIsNone(greeted.whom)
        self.assertIsNone(greeted.greeter)
