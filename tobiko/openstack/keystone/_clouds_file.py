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

import json
import os

from oslo_log import log
import yaml

import tobiko
from tobiko.openstack.keystone import _credentials


LOG = log.getLogger(__name__)

YAML_SUFFIXES = ('.yaml', '.yml')
JSON_SUFFIXES = ('.json',)
CLOUDS_FILE_SUFFIXES = JSON_SUFFIXES + YAML_SUFFIXES


class CloudsFileNotFoundError(tobiko.TobikoException):
    message = "No such clouds file(s): {clouds_files!s}"


class DefaultCloudsFileConfig(tobiko.SharedFixture):

    cloud_name = None
    clouds_file_dirs = None
    clouds_file_names = None
    clouds_files = None

    def setup_fixture(self):
        keystone_conf = tobiko.tobiko_config().keystone
        self.cloud_name = keystone_conf.cloud_name
        self.clouds_file_dirs = keystone_conf.clouds_file_dirs
        self.clouds_file_names = keystone_conf.clouds_file_names
        self.clouds_files = self.list_cloud_files()

    def list_cloud_files(self):
        cloud_files = []
        for directory in self.clouds_file_dirs:
            directory = tobiko.tobiko_config_path(directory)
            if os.path.isdir(directory):
                for file_name in self.clouds_file_names:
                    file_name = os.path.join(directory, file_name)
                    if os.path.isfile(file_name):
                        cloud_files.append(file_name)
        return cloud_files


class CloudsFileKeystoneCredentialsFixture(
        _credentials.KeystoneCredentialsFixture):

    cloud_name = None
    clouds_content = None
    clouds_file = None

    config = tobiko.required_setup_fixture(DefaultCloudsFileConfig)

    def __init__(self, credentials=None, cloud_name=None,
                 clouds_content=None, clouds_file=None, clouds_files=None):
        super(CloudsFileKeystoneCredentialsFixture, self).__init__(
            credentials=credentials)

        config = self.config
        if cloud_name is None:
            cloud_name = config.cloud_name
        self.cloud_name = cloud_name

        if clouds_content is not None:
            self.clouds_content = dict(clouds_content)

        if clouds_file is not None:
            self.clouds_file = clouds_file

        if clouds_files is None:
            clouds_files = config.clouds_files
        self.clouds_files = list(clouds_files)

    def get_credentials(self):
        cloud_name = self._get_cloud_name()
        if cloud_name is None:
            return None

        clouds_content = self._get_clouds_content()
        clouds_section = clouds_content.get("clouds")
        if clouds_section is None:
            message = ("'clouds' section not found in clouds file "
                       "{!r}").format(self.clouds_file)
            raise ValueError(message)

        clouds_config = clouds_section.get(cloud_name)
        if clouds_config is None:
            message = ("No such cloud with name {!r} in file "
                       "{!r}").format(cloud_name, self.clouds_file)
            raise ValueError(message)

        auth = clouds_config.get("auth")
        if auth is None:
            message = ("No such 'auth' section in cloud file {!r} for cloud "
                       "name {!r}").format(self.clouds_file, self.cloud_name)
            raise ValueError(message)

        auth_url = auth.get("auth_url")
        if not auth_url:
            message = ("No such 'auth_url' in file {!r} for cloud name "
                       "{!r}").format(self.clouds_file, self.cloud_name)
            raise ValueError(message)

        username = auth.get('username') or auth.get('user_id')
        password = auth.get('password')
        cacert = clouds_config.get('cacert')
        project_name = (auth.get('project_name') or
                        auth.get('tenant_namer') or
                        auth.get('project_id') or
                        auth.get_env('tenant_id'))

        api_version = (int(clouds_config.get("identity_api_version", 0)) or
                       _credentials.api_version_from_url(auth_url))
        if api_version == 2:
            return _credentials.keystone_credentials(
                api_version=api_version,
                auth_url=auth_url,
                username=username,
                password=password,
                project_name=project_name)

        else:
            domain_name = (auth.get("domain_name") or
                           auth.get("domain_id"))
            user_domain_name = (auth.get("user_domain_name") or
                                auth.get("user_domain_id"))
            project_domain_name = auth.get("project_domain_name")
            project_domain_id = auth.get("project_domain_id")
            trust_id = auth.get("trust_id")
            return _credentials.keystone_credentials(
                api_version=api_version,
                auth_url=auth_url,
                username=username,
                password=password,
                project_name=project_name,
                domain_name=domain_name,
                user_domain_name=user_domain_name,
                project_domain_name=project_domain_name,
                project_domain_id=project_domain_id,
                cacert=cacert,
                trust_id=trust_id)

    def _get_cloud_name(self):
        cloud_name = self.cloud_name
        if cloud_name is None:
            cloud_name = os.environ.get("OS_CLOUD")
            if cloud_name:
                LOG.debug("Got cloud name from 'OS_CLOUD' environment "
                          "variable: %r", cloud_name)
                self.cloud_name = cloud_name
            else:
                LOG.debug("Undefined environment variable: 'OS_CLOUD'")
        return cloud_name or None

    def _get_clouds_content(self):
        clouds_content = self.clouds_content
        if clouds_content is None:
            clouds_file = self._get_clouds_file()
            with open(clouds_file, 'r') as f:
                _, suffix = os.path.splitext(clouds_file)
                if suffix in JSON_SUFFIXES:
                    LOG.debug('Load JSON clouds file: %r', clouds_file)
                    clouds_content = json.load(f)
                else:
                    LOG.debug('Load YAML clouds file: %r', clouds_file)
                    clouds_content = yaml.safe_load(f)
            LOG.debug('Clouds file content loaded from %r:\n%s',
                      clouds_file, json.dumps(clouds_content,
                                              indent=4,
                                              sort_keys=True))
            self.clouds_content = clouds_content

        if not clouds_content:
            message = "Invalid clouds file content: {!r}".format(
                clouds_content)
            raise ValueError(message)
        return clouds_content

    def _get_clouds_file(self):
        clouds_file = self.clouds_file
        if clouds_file:
            clouds_files = [self.clouds_file]
        else:
            clouds_files = list(self.clouds_files)

        for filename in clouds_files:
            if os.path.exists(filename):
                LOG.debug('Found clouds file at %r', filename)
                self.clouds_file = clouds_file = filename
                break
        else:
            raise CloudsFileNotFoundError(clouds_files=', '.join(clouds_files))
        return clouds_file


_credentials.DEFAULT_KEYSTONE_CREDENTIALS_FIXTURES.insert(
    0, CloudsFileKeystoneCredentialsFixture)
