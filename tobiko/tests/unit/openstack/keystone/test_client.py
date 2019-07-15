# Copyright 2019 Red Hat
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

from keystoneclient.v2_0 import client as client_v2
from keystoneclient.v3 import client as client_v3

from tobiko.openstack import keystone
from tobiko.tests.unit import openstack
from tobiko.tests.unit.openstack import test_client


KEYSTONE_CLIENTS = client_v2.Client, client_v3.Client


class KeystoneClientFixtureTest(test_client.OpenstackClientFixtureTest):

    def create_client(self, session=None):
        return keystone.KeystoneClientFixture(session=session)


class GetKeystoneClientTest(openstack.OpenstackTest):

    def test_get_keystone_client(self, session=None, shared=True):
        client1 = keystone.get_keystone_client(session=session, shared=shared)
        client2 = keystone.get_keystone_client(session=session, shared=shared)
        if shared:
            self.assertIs(client1, client2)
        else:
            self.assertIsNot(client1, client2)
        self.assertIsInstance(client1, KEYSTONE_CLIENTS)
        self.assertIsInstance(client2, KEYSTONE_CLIENTS)

    def test_get_keystone_client_with_not_shared(self):
        self.test_get_keystone_client(shared=False)

    def test_get_keystone_client_with_session(self):
        session = keystone.get_keystone_session()
        self.test_get_keystone_client(session=session)


class KeystoneClientTest(openstack.OpenstackTest):

    def test_keystone_client_with_none(self):
        default_client = keystone.get_keystone_client()
        client = keystone.keystone_client(None)
        self.assertIsInstance(client, KEYSTONE_CLIENTS)
        self.assertIs(default_client, client)

    def test_keystone_client_with_client(self):
        default_client = keystone.get_keystone_client()
        client = keystone.keystone_client(default_client)
        self.assertIsInstance(client, KEYSTONE_CLIENTS)
        self.assertIs(default_client, client)

    def test_keystone_client_with_fixture(self):
        fixture = keystone.KeystoneClientFixture()
        client = keystone.keystone_client(fixture)
        self.assertIsInstance(client, KEYSTONE_CLIENTS)
        self.assertIs(client, fixture.client)
