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

from tobiko.tests import unit
from tobiko.openstack import keystone


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

V2_ENVIRON_WITH_VERSION = dict(V2_ENVIRON, OS_IDENTITY_API_VERSION='2')


V3_PARAMS = {
    'api_version': 3,
    'project_name': 'demo',
    'username': 'demo',
    'password': 'super-secret',
    'auth_url': 'http://10.0.0.1:5678/v3',
    'user_domain_name': 'demo',
    'project_domain_name': 'demo'}

V3_ENVIRON = {
    'OS_PROJECT_NAME': 'demo',
    'OS_USERNAME': 'demo',
    'OS_PASSWORD': 'super-secret',
    'OS_AUTH_URL': 'http://10.0.0.1:5678/v3',
    'OS_USER_DOMAIN_NAME': 'demo',
    'OS_PROJECT_DOMAIN_NAME': 'demo'}

V3_ENVIRON_WITH_VERSION = dict(V3_ENVIRON, OS_IDENTITY_API_VERSION='3')


def make_credentials(params, **kwargs):
    if kwargs:
        params = dict(params, **kwargs)
    return keystone.keystone_credentials(**params)


class KeystoneCredentialsTest(unit.TobikoUnitTest):

    def test_validate_from_params_v2(self):
        credentials = make_credentials(V2_PARAMS)
        credentials.validate()
        self.assertEqual(V2_PARAMS, credentials.to_dict())
        self.assertEqual(
            "keystone_credentials(auth_url='http://10.0.0.1:5678/v2.0', "
            "username='demo', project_name='demo', password='***', "
            "api_version=2)",
            repr(credentials))

    def test_validate_from_params_v3(self):
        credentials = make_credentials(V3_PARAMS)
        credentials.validate()
        self.assertEqual(V3_PARAMS, credentials.to_dict())
        self.assertEqual(
            "keystone_credentials(auth_url='http://10.0.0.1:5678/v3', "
            "username='demo', project_name='demo', password='***', "
            "api_version=3, user_domain_name='demo', "
            "project_domain_name='demo')",
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
