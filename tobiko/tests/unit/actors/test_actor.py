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

import typing

import tobiko
from tobiko.tests import unit
from tobiko import actors


class Greeter(actors.Actor):

    setup_called = False
    cleanup_called = False

    async def setup_actor(self):
        self.setup_called = True

    async def cleanup_actor(self):
        self.cleanup_called = True

    @actors.actor_method
    async def greet(self, whom: str, greeted: 'Greeted'):
        assert self.setup_called
        assert not self.cleanup_called
        if not whom:
            raise ValueError("'whom' parameter can't be empty")

        self.log.info(f"Hello {whom}!")
        await greeted.greeted(whom=whom, greeter=self)


class Greeted:

    greeter: typing.Optional[Greeter] = None
    whom: typing.Optional[str] = None

    async def greeted(self, whom: str, greeter: Greeter):
        self.greeter = greeter
        self.whom = whom


class ActorTest(unit.TobikoUnitTest):

    actor = tobiko.required_fixture(Greeter, setup=False)

    async def test_setup_actor(self):
        self.assertFalse(self.actor.setup_called)
        self.assertFalse(self.actor.cleanup_called)
        await actors.setup_actor(self.actor)
        self.assertTrue(self.actor.setup_called)
        self.assertFalse(self.actor.cleanup_called)

    async def test_cleanup_actor(self):
        self.assertFalse(self.actor.setup_called)
        self.assertFalse(self.actor.cleanup_called)
        await actors.cleanup_actor(self.actor)
        self.assertFalse(self.actor.setup_called)
        self.assertFalse(self.actor.cleanup_called)

    async def test_cleanup_actor_after_setup(self):
        await actors.setup_actor(self.actor)
        self.assertTrue(self.actor.setup_called)
        self.assertFalse(self.actor.cleanup_called)
        await actors.cleanup_actor(self.actor)
        self.assertTrue(self.actor.setup_called)
        self.assertTrue(self.actor.cleanup_called)

    async def test_ping_actor(self):
        ref = actors.start_actor(self.actor)
        result = await ref.ping_actor(self.id())
        self.assertEqual(self.id(), result)

    async def test_async_request(self):
        greeter = actors.start_actor(self.actor)
        self.assertIsInstance(greeter, actors.ActorRef[Greeter])
        greeted = Greeted()
        await greeter.greet(whom=self.id(), greeted=greeted)
        self.assertEqual(self.id(), greeted.whom)
        self.assertIs(self.actor, greeted.greeter)

    async def test_async_request_failure(self):
        greeter = actors.start_actor(self.actor)
        self.assertIsInstance(greeter, actors.ActorRef[Greeter])
        greeted = Greeted()

        try:
            await greeter.greet(whom="", greeted=greeted)
        except ValueError as ex:
            self.assertEqual("'whom' parameter can't be empty", str(ex))
        else:
            self.fail("Exception not raised")
        self.assertIsNone(greeted.whom)
        self.assertIsNone(greeted.greeter)
