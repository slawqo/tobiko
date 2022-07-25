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

import os

import testtools

import tobiko
from tobiko import config
from tobiko.openstack import keystone
from tobiko.tests.unit import openstack


V2_PARAMS = {
    'api_version': 2,
    'project_name': 'demo',
    'username': 'demo',
    'password': 'super-secret',
    'auth_url': 'http://10.0.0.1:5678/v2.0'}

V2_ENVIRON = {
    'OS_PROJECT_NAME': 'demo',
    'OS_USERNAME': 'demo',
    'OS_PASSWORD': 'super-secret',
    'OS_AUTH_URL': 'http://10.0.0.1:5678/v2.0'}

V2_ENVIRON_WITH_TENANT_NAME = {
    'OS_TENANT_NAME': 'demo',
    'OS_USERNAME': 'demo',
    'OS_PASSWORD': 'super-secret',
    'OS_AUTH_URL': 'http://10.0.0.1:5678/v2.0'}

V2_ENVIRON_WITH_VERSION = dict(V2_ENVIRON, OS_IDENTITY_API_VERSION='2')


V3_PARAMS = {
    'api_version': 3,
    'project_name': 'demo',
    'username': 'demo',
    'password': 'super-secret',
    'auth_url': 'http://10.0.0.1:5678/v3',
    'user_domain_name': 'Default',
    'project_domain_name': 'Default'}

V3_ENVIRON = {
    'OS_PROJECT_NAME': 'demo',
    'OS_USERNAME': 'demo',
    'OS_PASSWORD': 'super-secret',
    'OS_AUTH_URL': 'http://10.0.0.1:5678/v3',
    'OS_USER_DOMAIN_NAME': 'Default',
    'OS_PROJECT_DOMAIN_NAME': 'Default'}

V3_ENVIRON_WITH_VERSION = dict(V3_ENVIRON, OS_IDENTITY_API_VERSION='3')


def make_credentials(params, **kwargs):
    if kwargs:
        params = dict(params, **kwargs)
    return keystone.keystone_credentials(**params)


class KeystoneCredentialsTest(openstack.OpenstackTest):

    def test_validate_from_params_v2(self):
        credentials = make_credentials(V2_PARAMS)
        credentials.validate()
        self.assertEqual(V2_PARAMS, credentials.to_dict())
        self.assertEqual(
            "keystone_credentials("
            "api_version=2, "
            "auth_url='http://10.0.0.1:5678/v2.0', "
            "password='***', "
            "project_name='demo', "
            "username='demo')",
            repr(credentials))

    def test_validate_from_params_v3(self):
        credentials = make_credentials(V3_PARAMS)
        credentials.validate()
        self.assertEqual(V3_PARAMS, credentials.to_dict())
        self.assertEqual(
            "keystone_credentials("
            "api_version=3, "
            "auth_url='http://10.0.0.1:5678/v3', "
            "password='***', "
            "project_domain_name='Default', "
            "project_name='demo', "
            "user_domain_name='Default', "
            "username='demo')",
            repr(credentials))

    def test_validate_without_auth_url(self):
        credentials = make_credentials(V2_PARAMS, auth_url=None)
        self.assertRaises(keystone.InvalidKeystoneCredentials,
                          credentials.validate)

    def test_validate_without_username(self):
        credentials = make_credentials(V2_PARAMS, username=None)
        self.assertRaises(keystone.InvalidKeystoneCredentials,
                          credentials.validate)

    def test_validate_without_project_name(self):
        credentials = make_credentials(V2_PARAMS, project_name=None)
        self.assertRaises(keystone.InvalidKeystoneCredentials,
                          credentials.validate)

    def test_validate_without_password(self):
        credentials = make_credentials(V2_PARAMS, password=None)
        self.assertRaises(keystone.InvalidKeystoneCredentials,
                          credentials.validate)


class EnvironKeystoneCredentialsFixtureTest(openstack.OpenstackTest):

    def test_init(self):
        fixture = keystone.EnvironKeystoneCredentialsFixture()
        self.assertIsNone(fixture.credentials)

    def test_setup_with_no_credentials(self):
        fixture = keystone.EnvironKeystoneCredentialsFixture()
        self.assertRaises(keystone.NoSuchKeystoneCredentials,
                          tobiko.setup_fixture,
                          fixture)

    def test_setup_v2(self):
        self.patch(os, 'environ', V2_ENVIRON)
        fixture = keystone.EnvironKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V2_PARAMS, fixture.credentials.to_dict())

    def test_setup_v2_with_tenant_name(self):
        self.patch(os, 'environ', V2_ENVIRON_WITH_TENANT_NAME)
        fixture = keystone.EnvironKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V2_PARAMS, fixture.credentials.to_dict())

    def test_setup_v2_with_api_version(self):
        self.patch(os, 'environ', V2_ENVIRON_WITH_VERSION)
        fixture = keystone.EnvironKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V2_PARAMS, fixture.credentials.to_dict())

    def test_setup_v3(self):
        self.patch(os, 'environ', V3_ENVIRON)
        fixture = keystone.EnvironKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V3_PARAMS, fixture.credentials.to_dict())

    def test_setup_v3_without_api_version(self):
        self.patch(os, 'environ', V3_ENVIRON_WITH_VERSION)
        fixture = keystone.EnvironKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V3_PARAMS, fixture.credentials.to_dict())


class ConfigKeystoneCredentialsFixtureTest(openstack.OpenstackTest):

    def patch_config(self, params, **kwargs):
        credentials = make_credentials(params, **kwargs)
        return self.patch(config.CONF.tobiko, 'keystone', credentials)

    def test_init(self):
        fixture = keystone.ConfigKeystoneCredentialsFixture()
        self.assertIsNone(fixture.credentials)

    def test_setup_v2(self):
        self.patch_config(V2_PARAMS, api_version=None)
        fixture = keystone.ConfigKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V2_PARAMS, fixture.credentials.to_dict())

    def test_setup_v2_with_api_version(self):
        self.patch_config(V2_PARAMS, api_version=2)
        fixture = keystone.ConfigKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V2_PARAMS, fixture.credentials.to_dict())

    def test_setup_v3(self):
        self.patch_config(V3_PARAMS, api_version=None)
        fixture = keystone.ConfigKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V3_PARAMS, fixture.credentials.to_dict())

    def test_setup_v3_with_api_version(self):
        self.patch_config(V3_PARAMS, api_version=3)
        fixture = keystone.ConfigKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V3_PARAMS, fixture.credentials.to_dict())


class DelegateKeystoneCredentialsFixtureTest(openstack.OpenstackTest):

    def setUp(self):
        super().setUp()
        self.patch_config({})
        self.patch(os, 'environ', {})
        tobiko.remove_fixture(keystone.ConfigKeystoneCredentialsFixture)
        tobiko.remove_fixture(keystone.EnvironKeystoneCredentialsFixture)

    def patch_config(self, params, **kwargs):
        credentials = make_credentials(params, **kwargs)
        keystone_conf = tobiko.tobiko_config().keystone
        for name, value in credentials.to_dict().items():
            self.patch(keystone_conf, name, value)
        tobiko.tobiko_config().ssh.proxy_jump = None

    def test_init(self):
        fixture = keystone.DelegateKeystoneCredentialsFixture()
        self.assertIsNone(fixture.credentials)

    def test_setup_from_config(self):
        self.patch_config(V2_PARAMS)
        fixture = keystone.DelegateKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V2_PARAMS, fixture.credentials.to_dict())

    def test_setup_from_environ(self):
        self.patch(os, 'environ', V2_ENVIRON)
        fixture = keystone.DelegateKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V2_PARAMS, fixture.credentials.to_dict())

    def test_setup_from_environ_and_config(self):
        self.patch(os, 'environ', V3_ENVIRON)
        self.patch_config(V2_PARAMS)
        fixture = keystone.DelegateKeystoneCredentialsFixture()
        fixture.setUp()
        fixture.credentials.validate()
        self.assertEqual(V3_PARAMS, fixture.credentials.to_dict())


class SkipUnlessHasKeystoneCredentialsTest(openstack.OpenstackTest):

    def patch_has_keystone_credentials(self, return_value: bool):
        # pylint: disable=protected-access
        from tobiko.openstack.keystone import _credentials
        return self.patch(_credentials,
                          'has_keystone_credentials',
                          return_value=return_value)

    def test_skip_method_unless_has_keystone_credentials(self):
        has_keystone_credentials = self.patch_has_keystone_credentials(True)

        call_args = []

        @keystone.skip_unless_has_keystone_credentials()
        def decorated_func(*args, **kwargs):
            call_args.append([args, kwargs])

        has_keystone_credentials.assert_not_called()

        decorated_func(1, 2, a=1, b=2)

        # pylint: disable=no-member
        has_keystone_credentials.assert_called_once()
        self.assertEqual(call_args, [[(1, 2), {'a': 1, 'b': 2}]])

    def test_skip_class_unless_has_keystone_credentials(self):
        has_keystone_credentials = self.patch_has_keystone_credentials(True)

        calls = []

        @keystone.skip_unless_has_keystone_credentials()
        class SkipTest(testtools.TestCase):

            def test_skip(self):
                calls.append(True)

        has_keystone_credentials.assert_not_called()

        tobiko.run_test(SkipTest('test_skip'))

        has_keystone_credentials.assert_called_once()
        self.assertEqual(calls, [True])

    def test_skip_method_unless_has_keystone_credentials_without_creds(self):
        has_keystone_credentials = self.patch_has_keystone_credentials(False)

        @keystone.skip_unless_has_keystone_credentials()
        def decorated_func():
            self.fail('Not skipped')

        has_keystone_credentials.assert_not_called()

        self.assertRaises(self.skipException, decorated_func)
        has_keystone_credentials.assert_called_once()

    def test_skip_class_unless_has_keystone_credentials_without_creds(self):
        has_keystone_credentials = self.patch_has_keystone_credentials(False)

        @keystone.skip_unless_has_keystone_credentials()
        class SkipTest(testtools.TestCase):

            def test_skip(self):
                super(SkipTest, self).setUp()
                self.fail('Not skipped')

        case = SkipTest('test_skip')
        has_keystone_credentials.assert_not_called()

        result = tobiko.run_test(case=case)
        tobiko.assert_test_case_was_skipped(
            case,
            result=result,
            skip_reason='Missing Keystone credentials')
        has_keystone_credentials.assert_called_once()
