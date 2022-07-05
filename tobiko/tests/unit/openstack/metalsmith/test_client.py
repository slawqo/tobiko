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

from tobiko.openstack import keystone
from tobiko.openstack import metalsmith
from tobiko.tests.unit import openstack
from tobiko.tests.unit.openstack import test_client


class MetalsmithClientFixtureTest(test_client.OpenstackClientFixtureTest):

    def create_client(self, session=None):
        return metalsmith.MetalsmithClientFixture(session=session)


class GetMetalsmithClientTest(openstack.OpenstackTest):

    def test_get_metalsmith_client(self, session=None, shared=True):
        client1 = metalsmith.get_metalsmith_client(
            session=session, shared=shared)
        client2 = metalsmith.get_metalsmith_client(
            session=session, shared=shared)
        if shared:
            self.assertIs(client1, client2)
        else:
            self.assertIsNot(client1, client2)
        self.assertIsInstance(client1, metalsmith.CLIENT_CLASSES)
        self.assertIsInstance(client2, metalsmith.CLIENT_CLASSES)

    def test_get_metalsmith_client_with_not_shared(self):
        self.test_get_metalsmith_client(shared=False)

    def test_get_metalsmith_client_with_session(self):
        session = keystone.get_keystone_session()
        self.test_get_metalsmith_client(session=session)
