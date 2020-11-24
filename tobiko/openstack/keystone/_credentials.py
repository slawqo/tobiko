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
import os
import sys
import typing  # noqa

from oslo_log import log
import testtools
import yaml

import tobiko


LOG = log.getLogger(__name__)


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
                                'cacert',
                                'trust_id'])):

    def to_dict(self):
        return {k: v
                for k, v in self._asdict().items()
                if v is not None}

    def __repr__(self):
        params = self.to_dict()
        if 'password' in params:
            params['password'] = '***'
        return 'keystone_credentials({!s})'.format(
            ", ".join("{!s}={!r}".format(k, v)
                      for k, v in sorted(params.items())))

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


class NoSuchCredentialsError(tobiko.TobikoException):
    message = "No such credentials from any of: {fixtures}"


class KeystoneCredentialsFixture(tobiko.SharedFixture):

    credentials: typing.Optional[KeystoneCredentials] = None

    def __init__(self,
                 credentials: typing.Optional[KeystoneCredentials] = None):
        super(KeystoneCredentialsFixture, self).__init__()
        if credentials is not None:
            self.credentials = credentials

    def setup_fixture(self):
        self.setup_credentials()

    def setup_credentials(self):
        credentials = self.credentials
        if credentials is None:
            credentials = self.get_credentials()
            if credentials is not None:
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

    def get_credentials(self) -> typing.Optional[KeystoneCredentials]:
        return self.credentials


KeystoneCredentialsType = typing.Union[None,
                                       KeystoneCredentials,
                                       KeystoneCredentialsFixture,
                                       str,
                                       typing.Type]


def get_keystone_credentials(obj: KeystoneCredentialsType = None) -> \
        typing.Optional[KeystoneCredentials]:
    if obj is None:
        return default_keystone_credentials()
    if isinstance(obj, KeystoneCredentials):
        return obj
    if tobiko.is_fixture(obj):
        obj = tobiko.get_fixture(obj)
        if isinstance(obj, KeystoneCredentialsFixture):
            obj = tobiko.setup_fixture(obj).credentials
            return get_keystone_credentials(obj)
    raise TypeError(f"Can't get {KeystoneCredentials} object from {obj}")


def default_keystone_credentials() -> typing.Optional[KeystoneCredentials]:
    credentials = tobiko.setup_fixture(
        DefaultKeystoneCredentialsFixture).credentials
    if credentials is not None:
        tobiko.check_valid_type(credentials, KeystoneCredentials)
    return credentials


def keystone_credentials(api_version=None,
                         auth_url=None,
                         username=None,
                         password=None,
                         project_name=None,
                         domain_name=None,
                         user_domain_name=None,
                         project_domain_name=None,
                         project_domain_id=None,
                         cacert=None,
                         trust_id=None,
                         cls=KeystoneCredentials) -> KeystoneCredentials:
    return cls(api_version=api_version,
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


class InvalidKeystoneCredentials(tobiko.TobikoException):
    message = "invalid Keystone credentials; {reason!s}; {credentials!r}"


class EnvironKeystoneCredentialsFixture(KeystoneCredentialsFixture):

    environ: typing.Optional[typing.Dict[str, str]] = None

    def __init__(self,
                 credentials: typing.Optional[KeystoneCredentials] = None,
                 environ: typing.Optional[typing.Dict[str, str]] = None):
        super(EnvironKeystoneCredentialsFixture, self).__init__(
            credentials=credentials)
        if environ is not None:
            self.environ = environ

    def setup_fixture(self):
        if self.environ is None:
            self.environ = self.get_environ()
        super(EnvironKeystoneCredentialsFixture, self).setup_fixture()

    def get_environ(self) -> typing.Optional[typing.Dict[str, str]]:
        return dict(os.environ)

    def get_credentials(self) -> typing.Optional[KeystoneCredentials]:
        auth_url = self.get_env('OS_AUTH_URL')
        if not auth_url:
            LOG.debug("OS_AUTH_URL environment variable not defined")
            return None

        api_version = (
            self.get_int_env('OS_IDENTITY_API_VERSION') or
            api_version_from_url(auth_url))
        username = (
            self.get_env('OS_USERNAME') or
            self.get_env('OS_USER_ID'))
        password = self.get_env('OS_PASSWORD')
        project_name = (
            self.get_env('OS_PROJECT_NAME') or
            self.get_env('OS_TENANT_NAME') or
            self.get_env('OS_PROJECT_ID') or
            self.get_env('OS_TENANT_ID'))
        if api_version == 2:
            return keystone_credentials(
                api_version=api_version,
                auth_url=auth_url,
                username=username,
                password=password,
                project_name=project_name)
        else:
            domain_name = (
                self.get_env('OS_DOMAIN_NAME') or
                self.get_env('OS_DOMAIN_ID'))
            user_domain_name = (
                self.get_env('OS_USER_DOMAIN_NAME') or
                self.get_env('OS_USER_DOMAIN_ID'))
            project_domain_name = (
                self.get_env('OS_PROJECT_DOMAIN_NAME'))
            project_domain_id = (
                self.get_env('OS_PROJECT_DOMAIN_ID'))
            trust_id = self.get_env('OS_TRUST_ID')
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

    def get_env(self, name) -> typing.Optional[str]:
        environ = self.environ
        if environ is None:
            return None
        else:
            return environ.get(name)

    def get_int_env(self, name) -> typing.Optional[int]:
        value = self.get_env(name=name)
        if value is None:
            return None
        else:
            return int(value)


def has_keystone_credentials(obj=None) -> bool:
    try:
        credentials = get_keystone_credentials(obj)
    except NoSuchCredentialsError:
        return False
    else:
        return credentials is not None


def skip_unless_has_keystone_credentials(*args, **kwargs):
    return tobiko.skip_unless('Missing Keystone credentials',
                              has_keystone_credentials, *args, **kwargs)


class ConfigKeystoneCredentialsFixture(KeystoneCredentialsFixture):

    def get_credentials(self) -> typing.Optional[KeystoneCredentials]:
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

    def get_credentials(self) -> typing.Optional[KeystoneCredentials]:
        errors = []
        for fixture in self.fixtures:
            try:
                credentials = tobiko.setup_fixture(fixture).credentials
            except Exception as ex:
                LOG.debug("Error getting credentials from %r: %s",
                          tobiko.get_fixture_name(fixture), ex)
                errors.append(tobiko.exc_info())
                continue

            if credentials:
                LOG.info("Got default credentials from fixture %r: %r",
                         fixture, credentials)
                return credentials
            else:
                LOG.debug('Got no credentials from %r', fixture)

        if len(errors) == 1:
            errors[0].reraise()
        elif errors:
            raise testtools.MultipleExceptions(errors)

        raise NoSuchCredentialsError(fixtures=self.fixtures)


def api_version_from_url(auth_url) -> typing.Optional[int]:
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
