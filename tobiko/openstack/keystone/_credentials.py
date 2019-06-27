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

import collections
import sys

from oslo_log import log
import yaml

import tobiko


LOG = log.getLogger(__name__)


def get_keystone_credentials(obj=None):
    if not obj:
        return default_keystone_credentials()
    if tobiko.is_fixture(obj):
        obj = tobiko.get_fixture(obj)
        if isinstance(obj, KeystoneCredentialsFixture):
            obj = tobiko.setup_fixture(obj).credentials
    if isinstance(obj, KeystoneCredentials):
        return obj

    message = "Can't get {!r} object from {!r}".format(
        KeystoneCredentials, obj)
    raise TypeError(message)


def default_keystone_credentials():
    credentials = tobiko.setup_fixture(DefaultKeystoneCredentialsFixture
                                       ).credentials
    tobiko.check_valid_type(credentials, KeystoneCredentials)
    return credentials


class KeystoneCredentials(collections.namedtuple(
        'KeystoneCredentials', ['api_version',
                                'auth_url',
                                'username',
                                'password',
                                'project_name',
                                'domain_name',
                                'user_domain_name',
                                'project_domain_name',
                                'project_domain_id',
                                'trust_id'])):

    def to_dict(self):
        return collections.OrderedDict(
            (k, v)
            for k, v in self._asdict().items()
            if v is not None)

    def __repr__(self):
        params = self.to_dict()
        if 'password' in params:
            params['password'] = '***'
        return 'keystone_credentials({!s})'.format(
            ", ".join("{!s}={!r}".format(k, v)
                      for k, v in params.items()))

    required_params = ('auth_url', 'username', 'password', 'project_name')

    def validate(self, required_params=None):
        required_params = required_params or self.required_params
        missing_params = [p
                          for p in required_params
                          if not getattr(self, p)]
        if missing_params:
            reason = "undefined parameters: {!s}".format(
                ', '.join(missing_params))
            raise InvalidKeystoneCredentials(credentials=self, reason=reason)


def keystone_credentials(api_version=None,
                         auth_url=None,
                         username=None,
                         password=None,
                         project_name=None,
                         domain_name=None,
                         user_domain_name=None,
                         project_domain_name=None,
                         project_domain_id=None,
                         trust_id=None,
                         cls=KeystoneCredentials):
    return cls(api_version=api_version,
               auth_url=auth_url,
               username=username,
               password=password,
               project_name=project_name,
               domain_name=domain_name,
               user_domain_name=user_domain_name,
               project_domain_name=project_domain_name,
               project_domain_id=project_domain_id,
               trust_id=trust_id)


class InvalidKeystoneCredentials(tobiko.TobikoException):
    message = "invalid Keystone credentials; {reason!s}; {credentials!r}"


class KeystoneCredentialsFixture(tobiko.SharedFixture):

    credentials = None

    def __init__(self, credentials=None):
        super(KeystoneCredentialsFixture, self).__init__()
        if credentials:
            self.credentials = credentials

    def setup_fixture(self):
        self.setup_credentials()

    def setup_credentials(self):
        credentials = self.credentials
        if not self.credentials:
            credentials = self.get_credentials()
            if credentials:
                try:
                    credentials.validate()
                except InvalidKeystoneCredentials as ex:
                    LOG.info("No such valid credentials from %r (%r)",
                             self, ex)
                else:
                    self.addCleanup(self.cleanup_credentials)
                    self.credentials = credentials

    def cleanup_credentials(self):
        del self.credentials

    def get_credentials(self):
        return self.credentials


class EnvironKeystoneCredentialsFixture(KeystoneCredentialsFixture):

    def get_credentials(self):
        from tobiko import config
        auth_url = config.get_env('OS_AUTH_URL')
        if not auth_url:
            LOG.debug("OS_AUTH_URL environment variable not defined")
            return None

        api_version = (
            config.get_int_env('OS_IDENTITY_API_VERSION') or
            api_version_from_url(auth_url))
        username = (
            config.get_env('OS_USERNAME') or
            config.get_env('OS_USER_ID'))
        password = config.get_env('OS_PASSWORD')
        project_name = (
            config.get_env('OS_PROJECT_NAME') or
            config.get_env('OS_TENANT_NAME') or
            config.get_env('OS_PROJECT_ID') or
            config.get_env('OS_TENANT_ID'))
        if api_version == 2:
            return keystone_credentials(
                api_version=api_version,
                auth_url=auth_url,
                username=username,
                password=password,
                project_name=project_name)
        else:
            domain_name = (
                config.get_env('OS_DOMAIN_NAME') or
                config.get_env('OS_DOMAIN_ID'))
            user_domain_name = (
                config.get_env('OS_USER_DOMAIN_NAME') or
                config.get_env('OS_USER_DOMAIN_ID'))
            project_domain_name = (
                config.get_env('OS_PROJECT_DOMAIN_NAME'))
            project_domain_id = (
                config.get_env('OS_PROJECT_DOMAIN_ID'))
            trust_id = config.get_env('OS_TRUST_ID')
            return keystone_credentials(
                api_version=api_version,
                auth_url=auth_url,
                username=username,
                password=password,
                project_name=project_name,
                domain_name=domain_name,
                user_domain_name=user_domain_name,
                project_domain_name=project_domain_name,
                project_domain_id=project_domain_id,
                trust_id=trust_id)


class ConfigKeystoneCredentialsFixture(KeystoneCredentialsFixture):

    def get_credentials(self):
        from tobiko import config
        conf = config.CONF.tobiko.keystone
        auth_url = conf.auth_url
        if not auth_url:
            LOG.debug("auth_url option not defined in 'keystone' section of "
                      "tobiko.conf")
            return None

        api_version = (conf.api_version or
                       api_version_from_url(auth_url))
        if api_version == 2:
            return keystone_credentials(
                api_version=api_version,
                auth_url=auth_url,
                username=conf.username,
                password=conf.password,
                project_name=conf.project_name)
        else:
            return keystone_credentials(
                api_version=api_version,
                auth_url=auth_url,
                username=conf.username,
                password=conf.password,
                project_name=conf.project_name,
                domain_name=conf.domain_name,
                user_domain_name=conf.user_domain_name,
                project_domain_name=conf.project_domain_name,
                project_domain_id=conf.project_domain_id,
                trust_id=conf.trust_id)


DEFAULT_KEYSTONE_CREDENTIALS_FIXTURES = [
    EnvironKeystoneCredentialsFixture,
    ConfigKeystoneCredentialsFixture]


class DefaultKeystoneCredentialsFixture(KeystoneCredentialsFixture):

    fixtures = DEFAULT_KEYSTONE_CREDENTIALS_FIXTURES

    def get_credentials(self):
        for fixture in self.fixtures:
            try:
                credentials = tobiko.setup_fixture(fixture).credentials
            except Exception:
                LOG.exception("Error setting up fixture %r", fixture)
                continue

            if credentials:
                LOG.info("Got default credentials from fixture %r: %r",
                         fixture, credentials)
                return credentials


def api_version_from_url(auth_url):
    if auth_url.endswith('/v2.0'):
        LOG.debug('Got Keystone API version 2 from auth_url: %r', auth_url)
        return 2
    elif auth_url.endswith('/v3'):
        LOG.debug('Got Keystone API version 3 from auth_url: %r', auth_url)
        return 3
    else:
        LOG.warning('Unable to get Keystone API version from auth_url:  %r',
                    auth_url)
        return None


def print_credentials():
    credentials = default_keystone_credentials()
    yaml.dump(dict(credentials.to_dict()),
              sys.stdout,
              indent=4,
              sort_keys=True)
