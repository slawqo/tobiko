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

import json
import os
import tempfile
import typing  # noqa

import yaml

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack.keystone import _clouds_file
from tobiko.tests.unit import openstack
from tobiko.tests.unit.openstack.keystone import test_credentials


def make_clouds_content(cloud_name, api_version=None, auth=None):
    content = {}
    if api_version is not None:
        content['identity_api_version'] = api_version
    if auth is not None:
        content['auth'] = auth
    return {'clouds': {cloud_name: content}}


class CloudsFileFixture(tobiko.SharedFixture):

    cloud_name = None  # type: str
    api_version = None  # type: str
    auth = None  # type: typing.Dict[str, typing.Any]
    clouds_content = None
    clouds_file = None
    suffix = '.yaml'
    create_file = True

    def __init__(self, cloud_name=None, api_version=None, auth=None,
                 clouds_file=None, suffix=None, create_file=None,
                 clouds_content=None):
        super(CloudsFileFixture, self).__init__()
        if cloud_name is not None:
            self.cloud_name = cloud_name
        if api_version is not None:
            self.api_version = api_version
        if auth is not None:
            self.auth = auth
        if clouds_file is not None:
            self.clouds_file = clouds_file
        if suffix is not None:
            self.suffix = suffix
        if create_file is not None:
            self.create_file = create_file
        if clouds_content is not None:
            self.clouds_content = clouds_content

    def setup_fixture(self):
        clouds_content = self.clouds_content
        if clouds_content is None:
            self.clouds_content = clouds_content = make_clouds_content(
                cloud_name=self.cloud_name, api_version=self.api_version,
                auth=self.auth)

        if self.create_file:
            clouds_file = self.clouds_file
            if clouds_file is None:
                fd, clouds_file = tempfile.mkstemp(suffix=self.suffix)
                self.addCleanup(os.remove, clouds_file)
                self.clouds_file = clouds_file
                clouds_stream = os.fdopen(fd, 'wt')
            else:
                clouds_stream = os.open(clouds_file, 'wt')

            try:
                if self.suffix in _clouds_file.JSON_SUFFIXES:
                    json.dump(clouds_content, clouds_stream)
                elif self.suffix in _clouds_file.YAML_SUFFIXES:
                    yaml.safe_dump(clouds_content, clouds_stream)
            finally:
                clouds_stream.close()


class V2CloudsFileFixture(CloudsFileFixture):
    cloud_name = 'V2-TEST_CLOUD'
    auth = test_credentials.V2_PARAMS


class V3CloudsFileFixture(CloudsFileFixture):
    cloud_name = 'V3-TEST_CLOUD'
    auth = test_credentials.V3_PARAMS


class CloudsFileKeystoneCredentialsFixtureTest(openstack.OpenstackTest):

    config = tobiko.required_setup_fixture(
        _clouds_file.DefaultCloudsFileConfig)

    def test_init(self):
        fixture = keystone.CloudsFileKeystoneCredentialsFixture()
        self.assertEqual(self.config.cloud_name, fixture.cloud_name)
        self.assertIsNone(fixture.clouds_content)
        self.assertIsNone(fixture.clouds_file)
        self.assertEqual(self.config.clouds_files, fixture.clouds_files)

    def test_init_with_cloud_name(self):
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            cloud_name='cloud-name')
        self.assertEqual('cloud-name', fixture.cloud_name)

    def test_init_with_clouds_content(self):
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            clouds_content={})
        self.assertEqual({}, fixture.clouds_content)

    def test_init_with_clouds_file(self):
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            clouds_file='cloud-file')
        self.assertEqual('cloud-file', fixture.clouds_file)

    def test_init_with_clouds_files(self):
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            clouds_files=['a', 'b', 'd'])
        self.assertEqual(['a', 'b', 'd'], fixture.clouds_files)

    def test_setup_from_default_clouds_files(self):
        file_fixture = self.useFixture(V3CloudsFileFixture())
        self.patch(self.config, 'clouds_files',
                   ['/a', file_fixture.clouds_file, '/c'])
        credentials_fixture = self.useFixture(
            keystone.CloudsFileKeystoneCredentialsFixture(
                cloud_name=file_fixture.cloud_name))
        self.assertEqual(file_fixture.clouds_content,
                         credentials_fixture.clouds_content)
        self.assertEqual(test_credentials.V3_PARAMS,
                         credentials_fixture.credentials.to_dict())

    def test_setup_from_json(self):
        file_fixture = self.useFixture(V3CloudsFileFixture(suffix='.json'))
        credentials_fixture = self.useFixture(
            keystone.CloudsFileKeystoneCredentialsFixture(
                cloud_name=file_fixture.cloud_name,
                clouds_file=file_fixture.clouds_file))
        self.assertEqual(file_fixture.clouds_content,
                         credentials_fixture.clouds_content)
        self.assertEqual(test_credentials.V3_PARAMS,
                         credentials_fixture.credentials.to_dict())

    def test_setup_from_yaml(self):
        file_fixture = self.useFixture(V3CloudsFileFixture(suffix='.yaml'))
        credentials_fixture = self.useFixture(
            keystone.CloudsFileKeystoneCredentialsFixture(
                cloud_name=file_fixture.cloud_name,
                clouds_file=file_fixture.clouds_file))
        self.assertEqual(file_fixture.clouds_content,
                         credentials_fixture.clouds_content)
        self.assertEqual(test_credentials.V3_PARAMS,
                         credentials_fixture.credentials.to_dict())

    def test_setup_from_yml(self):
        file_fixture = self.useFixture(V3CloudsFileFixture(suffix='.yml'))
        credentials_fixture = self.useFixture(
            keystone.CloudsFileKeystoneCredentialsFixture(
                cloud_name=file_fixture.cloud_name,
                clouds_file=file_fixture.clouds_file))
        self.assertEqual(file_fixture.clouds_content,
                         credentials_fixture.clouds_content)
        self.assertEqual(test_credentials.V3_PARAMS,
                         credentials_fixture.credentials.to_dict())

    def test_setup_v2_credentials(self):
        file_fixture = self.useFixture(V2CloudsFileFixture())
        credentials_fixture = self.useFixture(
            keystone.CloudsFileKeystoneCredentialsFixture(
                cloud_name=file_fixture.cloud_name,
                clouds_file=file_fixture.clouds_file))
        self.assertEqual(file_fixture.clouds_content,
                         credentials_fixture.clouds_content)
        self.assertEqual(test_credentials.V2_PARAMS,
                         credentials_fixture.credentials.to_dict())

    def test_setup_with_cloud_name(self):
        file_fixture = self.useFixture(V3CloudsFileFixture())
        credentials_fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            cloud_name='cloud-name',
            clouds_file=file_fixture.clouds_file)
        ex = self.assertRaises(ValueError, tobiko.setup_fixture,
                               credentials_fixture)
        self.assertEqual("No such cloud with name 'cloud-name' in file " +
                         repr(file_fixture.clouds_file), str(ex))

    def test_setup_with_cloud_name_from_env(self):
        self.patch(self.config, 'cloud_name', None)

        file_fixture = self.useFixture(V2CloudsFileFixture())

        self.patch(os, 'environ', {'OS_CLOUD': file_fixture.cloud_name})
        credentials_fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            clouds_file=file_fixture.clouds_file)

        self.assertIsNone(credentials_fixture.cloud_name)
        tobiko.setup_fixture(credentials_fixture)
        self.assertEqual(file_fixture.cloud_name,
                         credentials_fixture.cloud_name)

    def test_setup_with_empty_cloud_name(self):
        file_fixture = self.useFixture(V2CloudsFileFixture())
        credentials_fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            clouds_file=file_fixture.clouds_file,
            cloud_name='')

        self.assertIsNone(credentials_fixture.credentials)
        self.assertEqual('', credentials_fixture.cloud_name)
        tobiko.setup_fixture(credentials_fixture)
        self.assertIsNone(credentials_fixture.credentials)
        self.assertEqual('', credentials_fixture.cloud_name)

    def test_setup_with_empty_cloud_name_from_env(self):
        self.patch(self.config, 'cloud_name', None)

        file_fixture = self.useFixture(V2CloudsFileFixture())
        self.patch(os, 'environ', {'OS_CLOUD': ''})
        credentials_fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            clouds_file=file_fixture.clouds_file)

        self.assertIsNone(credentials_fixture.credentials)
        self.assertIsNone(credentials_fixture.cloud_name)
        tobiko.setup_fixture(credentials_fixture)
        self.assertIsNone(credentials_fixture.credentials)
        self.assertIsNone(credentials_fixture.cloud_name)

    def test_setup_with_no_cloud_name(self):
        self.patch(self.config, 'cloud_name', None)

        file_fixture = self.useFixture(V2CloudsFileFixture())
        credentials_fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            clouds_file=file_fixture.clouds_file)

        self.assertIsNone(credentials_fixture.credentials)
        self.assertIsNone(credentials_fixture.cloud_name)
        tobiko.setup_fixture(credentials_fixture)
        self.assertIsNone(credentials_fixture.credentials)
        self.assertIsNone(credentials_fixture.cloud_name)

    def test_setup_with_no_clouds_section(self):
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            cloud_name='cloud-name', clouds_content={'other_data': None},
            clouds_file='clouds-file')
        ex = self.assertRaises(ValueError, tobiko.setup_fixture, fixture)
        self.assertEqual('cloud-name', fixture.cloud_name)
        self.assertEqual({'other_data': None}, fixture.clouds_content)
        self.assertEqual("'clouds' section not found in clouds file "
                         "'clouds-file'", str(ex))

    def test_setup_with_empty_clouds_content(self):
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            cloud_name='cloud-name', clouds_content={})
        ex = self.assertRaises(ValueError, tobiko.setup_fixture, fixture)
        self.assertEqual('cloud-name', fixture.cloud_name)
        self.assertEqual({}, fixture.clouds_content)
        self.assertEqual('Invalid clouds file content: {}', str(ex))

    def test_setup_with_no_auth(self):
        clouds_content = make_clouds_content('cloud-name')
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            cloud_name='cloud-name',
            clouds_content=clouds_content,
            clouds_file='cloud-file')
        ex = self.assertRaises(ValueError, tobiko.setup_fixture, fixture)
        self.assertEqual('cloud-name', fixture.cloud_name)
        self.assertEqual(
            "No such 'auth' section in cloud file 'cloud-file' for cloud "
            "name 'cloud-name'", str(ex))

    def test_setup_with_no_auth_url(self):
        clouds_content = make_clouds_content('cloud-name', auth={})
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            cloud_name='cloud-name',
            clouds_content=clouds_content,
            clouds_file='cloud-file')
        ex = self.assertRaises(ValueError, tobiko.setup_fixture, fixture)
        self.assertEqual('cloud-name', fixture.cloud_name)
        self.assertEqual(
            "No such 'auth_url' in file 'cloud-file' for cloud name "
            "'cloud-name'", str(ex))

    def test_setup_without_clouds_file(self):
        self.patch(self.config, 'clouds_files', ['/a', '/b', '/c'])
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            cloud_name='cloud-name')
        ex = self.assertRaises(_clouds_file.CloudsFileNotFoundError,
                               tobiko.setup_fixture, fixture)
        self.assertEqual('cloud-name', fixture.cloud_name)
        self.assertEqual("No such clouds file(s): /a, /b, /c", str(ex))

    def test_setup_with_non_existing_clouds_file(self):
        fixture = keystone.CloudsFileKeystoneCredentialsFixture(
            clouds_file='/a.yaml',
            cloud_name='cloud-name')
        ex = self.assertRaises(_clouds_file.CloudsFileNotFoundError,
                               tobiko.setup_fixture, fixture)
        self.assertEqual("No such clouds file(s): /a.yaml", str(ex))
