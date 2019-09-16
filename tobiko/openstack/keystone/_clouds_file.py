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

import appdirs
from oslo_log import log
import yaml

from tobiko.openstack.keystone import _credentials


LOG = log.getLogger(__name__)

APPDIRS = appdirs.AppDirs('openstack', 'OpenStack', multipath='/etc')

CONFIG_SEARCH_PATH = [os.getcwd(),
                      APPDIRS.user_config_dir,
                      os.path.expanduser('~/.config/openstack'),
                      APPDIRS.site_config_dir,
                      '/etc/openstack']
YAML_SUFFIXES = ('.yaml', '.yml')
JSON_SUFFIXES = ('.json',)
DEFAULT_CLOUDS_FILES = [
    os.path.join(d, 'clouds' + s)
    for d in CONFIG_SEARCH_PATH
    for s in YAML_SUFFIXES + JSON_SUFFIXES]


try:
    FileNotFound = FileNotFoundError
except NameError:
    FileNotFound = OSError


class CloudsFileKeystoneCredentialsFixture(
        _credentials.KeystoneCredentialsFixture):

    cloud_name = None
    clouds_content = None
    clouds_file = None

    def __init__(self, credentials=None, cloud_name=None,
                 clouds_content=None, clouds_file=None, clouds_files=None):
        super(CloudsFileKeystoneCredentialsFixture, self).__init__(
            credentials=credentials)
        if cloud_name is not None:
            self.cloud_name = cloud_name
        if clouds_content is not None:
            self.clouds_content = dict(clouds_content)
        if clouds_file is not None:
            self.clouds_file = clouds_file
        if clouds_files is None:
            self.clouds_files = tuple(DEFAULT_CLOUDS_FILES)
        else:
            self.clouds_files = tuple(clouds_files)

    def get_credentials(self):
        cloud_name = self._get_cloud_name()
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

        api_version = (int(clouds_config.get("identity_api_version", 0)) or
                       _credentials.api_version_from_url(auth_url))
        if api_version == 2:
            return _credentials.keystone_credentials(
                api_version=api_version,
                auth_url=auth_url,
                username=auth.get("username"),
                password=auth.get("password"),
                project_name=auth.get("project_name"))
        else:
            return _credentials.keystone_credentials(
                api_version=api_version,
                auth_url=auth_url,
                username=auth.get("username"),
                password=auth.get("password"),
                project_name=auth.get("project_name"),
                domain_name=auth.get("domain_name"),
                user_domain_name=auth.get("user_domain_name"),
                project_domain_name=auth.get("project_domain_name"),
                project_domain_id=auth.get("project_domain_id"),
                trust_id=auth.get("trust_id"))

    def _get_cloud_name(self):
        cloud_name = self.cloud_name
        if cloud_name is None:
            cloud_name = os.environ.get("OS_CLOUD")
            if cloud_name:
                LOG.debug("Got cloud name from 'OS_CLOUD' environment "
                          "variable: %r", cloud_name)
                self.cloud_name = cloud_name
            else:
                message = "Undefined environment variable: 'OS_CLOUD'"
                raise ValueError(message)
        if not cloud_name:
            message = "Invalid cloud name: {!r}".format(cloud_name)
            raise ValueError(message)
        return cloud_name

    def _get_clouds_content(self):
        clouds_content = self.clouds_content
        if clouds_content is None:
            clouds_file = self._get_clouds_file()
            with open(clouds_file, 'r') as f:
                _, suffix = os.path.splitext(clouds_file)
                if suffix in JSON_SUFFIXES:
                    LOG.debug('Load JSON clouds file: %r', clouds_file)
                    clouds_content = json.load(f)
                elif suffix in YAML_SUFFIXES:
                    LOG.debug('Load YAML clouds file: %r', clouds_file)
                    clouds_content = yaml.safe_load(f)
                else:
                    message = 'Invalid clouds file suffix: {!r}'.format(
                        suffix)
                    raise ValueError(message)
            LOG.debug('Clouds file content loaded from %r:\n%r',
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
        if not clouds_file:
            clouds_files = self.clouds_files
            for filename in clouds_files:
                if os.path.exists(filename):
                    LOG.debug('Found clouds file at %r', filename)
                    self.clouds_file = clouds_file = filename
                    break
            else:
                message = 'No such clouds file: {!s}'.format(
                    ', '.join(repr(f) for f in clouds_files))
                raise FileNotFound(message)

        if not os.path.exists(clouds_file):
            message = 'Cloud file not found: {!r}'.format(clouds_file)
            raise FileNotFound(message)

        return clouds_file


_credentials.DEFAULT_KEYSTONE_CREDENTIALS_FIXTURES.insert(
    0, CloudsFileKeystoneCredentialsFixture)
