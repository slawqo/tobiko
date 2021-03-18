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

from unittest import mock

import tobiko
from tobiko.tests import unit
from tobiko import actor


class Greeter(tobiko.Protocol):

    async def greet(self, whom: str, greeted: 'Greeted'):
        raise NotImplementedError


class Greeted(tobiko.Protocol):

    def greeted(self, whom: str, greeter: Greeter):
        raise NotImplementedError


class GreeterActor(Greeter, actor.Actor):

    setup_called = False
    cleanup_called = False

    async def setup_actor(self):
        self.setup_called = True

    async def cleanup_actor(self):
        self.cleanup_called = True

    @actor.actor_method
    async def greet(self, whom: str, greeted: Greeted):
        assert self.setup_called
        assert not self.cleanup_called
        if not whom:
            raise ValueError("'whom' parameter can't be empty")

        self.log.info(f"Hello {whom}!")
        greeted.greeted(whom=whom, greeter=self.ref.get_interface(Greeter))


class ActorTest(unit.TobikoUnitTest):

    async def test_async_request(self):
        actor_ref = actor.create_actor(GreeterActor)
        self.assertIsInstance(actor_ref, actor.ActorRef)
        greeter = actor_ref.get_interface(Greeter)
        self.assertIsInstance(greeter, Greeter)
        greeted = mock.MagicMock(spec=Greeted)

        await greeter.greet(whom=self.id(), greeted=greeted)
        greeted.greeted.assert_called_with(whom=self.id(),
                                           greeter=greeter)

    async def test_async_request_failure(self):
        actor_ref = actor.create_actor(GreeterActor)
        self.assertIsInstance(actor_ref, actor.ActorRef)
        greeter = actor_ref.get_interface(Greeter)
        self.assertIsInstance(greeter, Greeter)
        greeted = mock.MagicMock(spec=Greeted)

        try:
            await greeter.greet(whom="", greeted=greeted)
        except ValueError as ex:
            self.assertEqual("'whom' parameter can't be empty", str(ex))
        else:
            self.fail("Exception not raised")
        greeted.greeted.assert_not_called()
