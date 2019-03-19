# Copyright (c) 2019 Red Hat
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

import inspect

import tobiko

from tobiko.openstack import keystone
from tobiko.tests import unit


CREDENTIALS = keystone.keystone_credentials(
    api_version=3,
    auth_url='http://127.0.0.1:4000/identiy/v3',
    username='demo',
    project_name='demo',
    password='this is a secret',
    user_domain_name='Default',
    project_domain_name='Default')


class CredentialsFixture(tobiko.SharedFixture):

    credentials = None

    def setup_fixture(self):
        self.credentials = CREDENTIALS


class DefaultCredentialsFixture(tobiko.SharedFixture):

    credentials = None

    def setup_fixture(self):
        self.credentials = DEFAULT_CREDENTIALS


DEFAULT_CREDENTIALS = keystone.keystone_credentials(
    api_version=2,
    auth_url='http://127.0.0.1:5000/identiy/v2.0',
    username='admin',
    project_name='admin',
    password='this is a secret')


class KeystoneSessionFixtureTest(unit.TobikoUnitTest):

    default_credentials_fixture = (
        'tobiko.openstack.keystone.credentials.'
        'DefaultKeystoneCredentialsFixture')

    def setUp(self):
        super(KeystoneSessionFixtureTest, self).setUp()
        tobiko.remove_fixture(self.default_credentials_fixture)
        self.patch(self.default_credentials_fixture,
                   DefaultCredentialsFixture)

    def test_init(self, credentials=None):
        session = keystone.KeystoneSessionFixture(credentials=credentials)
        if credentials:
            if tobiko.is_fixture(credentials):
                self.assertIsNone(session.credentials)
                self.assertIs(credentials, session.credentials_fixture)
            else:
                self.assertIs(credentials, session.credentials)
                self.assertIsNone(session.credentials_fixture)
        else:
            self.assertIsNone(session.credentials)
            self.assertIsNone(session.credentials_fixture)
        return session

    def test_init_with_credentials(self):
        self.test_init(credentials=CREDENTIALS)

    def test_init_with_credentials_fixture(self):
        self.test_init(credentials=CredentialsFixture())

    def test_init_with_credentials_fixture_type(self):
        self.test_init(credentials=CredentialsFixture)

    def test_setup(self, credentials=None):
        session = keystone.KeystoneSessionFixture(credentials=credentials)
        session.setUp()
        if credentials:
            if tobiko.is_fixture(credentials):
                if inspect.isclass(credentials):
                    credentials = tobiko.get_fixture(credentials)
                self.assertIs(credentials.credentials, session.credentials)
            else:
                self.assertIs(credentials, session.credentials)
        else:
            self.assertEqual(DEFAULT_CREDENTIALS, session.credentials)

    def test_setup_with_credentials(self):
        self.test_setup(credentials=CREDENTIALS)

    def test_setup_with_credentials_fixture(self):
        self.test_setup(credentials=CredentialsFixture())

    def test_setup_with_credentials_fixture_type(self):
        self.test_setup(credentials=CredentialsFixture)
