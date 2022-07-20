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

import functools
import json
import sys
import typing

from oslo_log import log

import tobiko
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


_REQUIRED_CREDENTIALS_PARAMS = (
    'auth_url', 'username', 'password', 'project_name')


class KeystoneCredentials(typing.NamedTuple):
    auth_url: str
    username: str
    password: str
    project_name: str

    api_version: typing.Optional[int] = None
    domain_name: typing.Optional[str] = None
    user_domain_name: typing.Optional[str] = None
    project_domain_name: typing.Optional[str] = None
    project_domain_id: typing.Optional[str] = None
    cacert: typing.Optional[str] = None
    trust_id: typing.Optional[str] = None

    def to_dict(self) -> typing.Dict[str, typing.Any]:
        # pylint: disable=no-member
        return {k: v
                for k, v in self._asdict().items()
                if v is not None}

    def to_json(self, indent=4, sort_keys=True) -> str:
        return json.dumps(self.to_dict(),
                          sort_keys=sort_keys,
                          indent=indent)

    def __repr__(self):
        params = self.to_dict()
        if 'password' in params:
            params['password'] = '***'
        params_dump = ', '.join(f"{name}={value!r}"
                                for name, value in sorted(params.items()))
        return f'keystone_credentials({params_dump})'

    def validate(self, required_params: typing.Iterable[str] = None):
        if required_params is None:
            required_params = _REQUIRED_CREDENTIALS_PARAMS
        missing_params = [p
                          for p in required_params
                          if not getattr(self, p)]
        if missing_params:
            reason = "undefined parameters: {!s}".format(
                ', '.join(missing_params))
            raise InvalidKeystoneCredentials(credentials=self, reason=reason)


class NoSuchKeystoneCredentials(tobiko.ObjectNotFound):
    message = "no such credentials. {reason}"


class KeystoneCredentialsFixture(tobiko.SharedFixture):

    def __init__(self,
                 credentials: KeystoneCredentials = None,
                 connection: sh.ShellConnectionType = None,
                 environ: typing.Dict[str, str] = None):
        super().__init__()
        self.credentials = credentials
        self._connection = connection
        self._environ = environ

    @property
    def connection(self) -> sh.ShellConnection:
        if self._connection is None:
            self._connection = self._get_connection()
            self.addCleanup(self._cleanup_connection)
        if not isinstance(self._connection, sh.ShellConnection):
            self._connection = sh.shell_connection(self._connection)
        return self._connection

    @property
    def environ(self) -> typing.Dict[str, str]:
        if self._environ is None:
            environ = self._get_environ()
            self._environ = {
                name: value
                for name, value in environ.items()
                if name.startswith('OS_')}
            self.addCleanup(self._cleanup_environ)
        return self._environ

    @property
    def login(self):
        return self.connection.login

    def setup_fixture(self):
        self.setup_credentials()
        assert self.credentials is not None
        self.credentials.validate()

    def setup_credentials(self) -> KeystoneCredentials:
        if self.credentials is None:
            LOG.debug('Getting credentials...\n'
                      f"  login: {self.login}\n"
                      f"  fixture: {tobiko.get_fixture_name(self)}\n")
            self.credentials = self._get_credentials()
            assert self.credentials is not None
            credentials_dump = json.dumps(self.credentials.to_dict(),
                                          sort_keys=True,
                                          indent=4)
            LOG.debug('Got credentials:\n'
                      f"  login: {self.login}\n"
                      f"  fixture: {tobiko.get_fixture_name(self)}\n"
                      "  credentials:\n"
                      f"{credentials_dump}\n")
            self.addCleanup(self._cleanup_credentials)
        return self.credentials

    def _get_credentials(self) -> KeystoneCredentials:
        raise NoSuchKeystoneCredentials(
            reason=f"[{self.fixture_name}] credentials not assigned")

    def _cleanup_credentials(self):
        self.credentials = None

    def _get_connection(self) -> sh.ShellConnectionType:
        return sh.local_shell_connection()

    def _cleanup_connection(self):
        self._connection = None

    def _get_environ(self) -> typing.Dict[str, str]:
        return self.connection.get_environ()

    def _cleanup_environ(self):
        self._environ = None

    def __repr__(self) -> str:
        return f'<{self.fixture_name} {self.login}>'


KeystoneCredentialsType = typing.Union[
    KeystoneCredentials,
    KeystoneCredentialsFixture,
    typing.Type[KeystoneCredentialsFixture]]


def keystone_credentials(credentials: KeystoneCredentialsType = None,
                         **params) \
        -> KeystoneCredentials:
    if credentials is None:
        if params:
            credentials = KeystoneCredentials(**params)
            params = {}
        else:
            credentials = default_keystone_credentials()
    assert credentials is not None

    if tobiko.is_fixture(credentials):
        credentials = tobiko.get_fixture(credentials)
        if isinstance(credentials, KeystoneCredentialsFixture):
            credentials = tobiko.setup_fixture(credentials).credentials
    assert isinstance(credentials, KeystoneCredentials)
    if params:
        params = credentials.to_dict()
        params.update(**params)
        credentials = KeystoneCredentials(**params)
    return credentials


def default_keystone_credentials() -> KeystoneCredentials:
    return tobiko.setup_fixture(
        DelegateKeystoneCredentialsFixture).credentials


class InvalidKeystoneCredentials(tobiko.TobikoException):
    message = "invalid Keystone credentials; {reason!s}; {credentials!r}"


class EnvironKeystoneCredentialsFixture(KeystoneCredentialsFixture):

    def _get_credentials(self) -> KeystoneCredentials:
        auth_url = self.get_env('OS_AUTH_URL')
        if not auth_url:
            raise NoSuchKeystoneCredentials(
                reason=(f"[{self.fixture_name}] OS_AUTH_URL environment "
                        f"variable is {auth_url!r}"))

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
        return self.environ.get(name)

    def get_int_env(self, name) -> typing.Optional[int]:
        value = self.get_env(name=name)
        if value is None:
            return None
        else:
            return int(value)


@functools.lru_cache()
def has_keystone_credentials(obj: KeystoneCredentialsType = None) -> bool:
    try:
        credentials = keystone_credentials(obj)
    except NoSuchKeystoneCredentials:
        LOG.debug('Openstack Keystone credentials not found', exc_info=True)
        return False
    else:
        LOG.debug(f'Openstack Keystone credentials found: {credentials!r}')
        return True


def skip_unless_has_keystone_credentials(*args, **kwargs):
    return tobiko.skip_unless('Missing Keystone credentials',
                              has_keystone_credentials, *args, **kwargs)


class ConfigKeystoneCredentialsFixture(KeystoneCredentialsFixture):

    def _get_credentials(self) -> KeystoneCredentials:
        conf = tobiko.tobiko_config().keystone
        auth_url = conf.auth_url
        if not auth_url:
            raise NoSuchKeystoneCredentials(
                reason="'auth_url' option not defined in 'keystone' section "
                       "of 'tobiko.conf' file")

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


class DelegateKeystoneCredentialsFixture(KeystoneCredentialsFixture):

    def __init__(self,
                 delegates: typing.Iterable[KeystoneCredentialsFixture] = None,
                 credentials: KeystoneCredentials = None,
                 connection: sh.ShellConnectionType = None,
                 environ: typing.Dict[str, str] = None):
        super().__init__(credentials=credentials,
                         connection=connection,
                         environ=environ)
        if delegates is not None:
            delegates = list(delegates)
        self._delegates = delegates

    @property
    def delegates(self) -> typing.List[KeystoneCredentialsFixture]:
        if self._delegates is None:
            self._delegates = self._get_delegates()
        return self._delegates

    @staticmethod
    def _get_delegates() -> typing.List[KeystoneCredentialsFixture]:
        from tobiko.openstack.keystone import _clouds_file

        delegates: typing.List[KeystoneCredentialsFixture] = []

        keystone_conf = tobiko.tobiko_config().keystone
        hosts = keystone_conf.clouds_file_hosts
        if hosts:
            for host in hosts:
                delegates.append(
                    _clouds_file.CloudsFileKeystoneCredentialsFixture(
                        connection=host))

        proxy_client = ssh.ssh_proxy_client()
        if proxy_client is not None:
            delegates.append(
                _clouds_file.CloudsFileKeystoneCredentialsFixture(
                    connection=proxy_client))

        delegates.append(
            tobiko.get_fixture(EnvironKeystoneCredentialsFixture))
        delegates.append(
            tobiko.get_fixture(ConfigKeystoneCredentialsFixture))
        return delegates

    def _get_credentials(self) -> KeystoneCredentials:
        for delegate in self.delegates:
            try:
                return tobiko.setup_fixture(delegate).credentials
            except NoSuchKeystoneCredentials as ex:
                LOG.debug(f'Got no credentials from {delegate!r}:\n'
                          f'    {ex}\n')
        raise NoSuchKeystoneCredentials(
            reason=f'[{self.fixture_name}] no credentials from '
                   f'delegates: {self.delegates!r}')


def register_default_keystone_credentials(
        credentials: KeystoneCredentialsFixture,
        delegate: DelegateKeystoneCredentialsFixture = None,
        position: int = None):
    if delegate is None:
        delegate = tobiko.get_fixture(DelegateKeystoneCredentialsFixture)
    tobiko.check_valid_type(credentials, KeystoneCredentialsFixture)
    if position is None:
        delegate.delegates.append(credentials)
    else:
        delegate.delegates.insert(position, credentials)


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


def print_credentials(credentials: KeystoneCredentialsType = None):
    credentials = keystone_credentials(credentials)
    tobiko.dump_yaml(dict(credentials.to_dict()),
                     sys.stdout,
                     indent=4,
                     sort_keys=True)
