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

from keystoneclient import discover
from keystoneclient.v2_0 import client as client_v2
from keystoneclient.v3 import client as client_v3
from oslo_log import log

from tobiko.openstack import keystone
from tobiko.tests.unit import openstack
from tobiko.tests.unit.openstack import test_client

LOG = log.getLogger(__name__)
KEYSTONE_CLIENTS = client_v2.Client, client_v3.Client


class DiscoverMock(object):

    def __init__(self, session, **kwargs):
        self.session = session
        self.kwargs = kwargs

    def create_client(self, version, unstable):
        LOG.debug("Create a mock keystone client for version %r "
                  "(unestable=%r)", version, unstable)
        return client_v3.Client(session=self.session)


class KeystoneClientFixtureTest(test_client.OpenstackClientFixtureTest):

    def setUp(self):
        super(KeystoneClientFixtureTest, self).setUp()
        self.patch(discover, 'Discover', DiscoverMock)

    def create_client(self, session=None):
        return keystone.KeystoneClientFixture(session=session)


class GetKeystoneClientTest(openstack.OpenstackTest):

    def setUp(self):
        super(GetKeystoneClientTest, self).setUp()
        self.patch(discover, 'Discover', DiscoverMock)

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

    def setUp(self):
        super(KeystoneClientTest, self).setUp()
        self.patch(discover, 'Discover', DiscoverMock)

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
