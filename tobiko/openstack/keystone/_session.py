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

import typing

from keystoneauth1 import loading
from keystoneauth1 import session as _session
from keystoneauth1 import plugin as _plugin
from oslo_log import log

import tobiko
from tobiko.openstack.keystone import _credentials
from tobiko import http


LOG = log.getLogger(__name__)

KEYSTONE_SESSION_CLASSES = _session.Session,
KeystoneSession = typing.Union[_session.Session]


class KeystoneSessionFixture(tobiko.SharedFixture):

    VALID_CREDENTIALS_TYPES = (_credentials.KeystoneCredentials,
                               _credentials.KeystoneCredentialsFixture,
                               type)

    def __init__(self,
                 credentials: _credentials.KeystoneCredentialsType = None,
                 session: KeystoneSession = None):
        super(KeystoneSessionFixture, self).__init__()
        if credentials is not None:
            tobiko.check_valid_type(credentials, *self.VALID_CREDENTIALS_TYPES)
        self._credentials = credentials
        self.session = session

    @property
    def credentials(self) -> _credentials.KeystoneCredentials:
        if self._credentials is None:
            self._credentials = self._get_credentials()
        elif not isinstance(self._credentials,
                            _credentials.KeystoneCredentials):
            self._credentials = _credentials.keystone_credentials(
                self._credentials)
        return self._credentials

    def setup_fixture(self):
        self.setup_session()

    def setup_session(self):
        if self.session is None:
            self.session = self._get_session()

    def _get_session(self) -> KeystoneSession:
        credentials = self.credentials
        LOG.debug("Create Keystone session from credentials "
                  f"{credentials}")
        credentials.validate()
        loader = loading.get_plugin_loader('password')
        params = credentials.to_dict()
        # api version parameter is not accepted
        params.pop('api_version', None)
        params.pop('cacert', None)
        auth = loader.load_from_options(**params)
        session = _session.Session(auth=auth, verify=False)
        http.setup_http_session(session)
        return session

    @staticmethod
    def _get_credentials() -> _credentials.KeystoneCredentials:
        return _credentials.default_keystone_credentials()


KeystoneSessionType = typing.Union[KeystoneSession,
                                   KeystoneSessionFixture,
                                   typing.Type[KeystoneSessionFixture]]


def keystone_session(obj: KeystoneSessionType = None) -> KeystoneSession:
    if obj is None:
        return default_keystone_session()
    if tobiko.is_fixture(obj):
        obj = tobiko.get_fixture(obj)
        if isinstance(obj, KeystoneSessionFixture):
            obj = tobiko.setup_fixture(obj).session
    return tobiko.check_valid_type(obj, KEYSTONE_SESSION_CLASSES)


InitSessionType = typing.Callable[[_credentials.KeystoneCredentials],
                                  KeystoneSessionFixture]


class KeystoneSessionManager(object):

    def __init__(self):
        self.sessions: typing.Dict[_credentials.KeystoneCredentials,
                                   KeystoneSessionFixture] = {}

    def get_session(self,
                    credentials: _credentials.KeystoneCredentialsType = None,
                    init_session: InitSessionType = None,
                    shared: bool = True) \
            -> KeystoneSessionFixture:
        credentials = _credentials.keystone_credentials(credentials)
        if shared:
            session = self.sessions.get(credentials)
            if session is not None:
                return session
        session = self.create_session(credentials=credentials,
                                      init_session=init_session)
        if shared:
            self.sessions[credentials] = session
        return session

    def create_session(self,
                       credentials: _credentials.KeystoneCredentials,
                       init_session: InitSessionType = None) \
            -> KeystoneSessionFixture:
        if init_session is None:
            init_session = self.init_session
        assert callable(init_session)
        LOG.debug('Initialize Keystone session:\n'
                  f"  init_session: {init_session}\n"
                  f"  credentials: {credentials}\n")
        session = init_session(credentials)
        LOG.debug('Got new Keystone session:\n'
                  f"  init_session: {init_session}\n"
                  f"  credentials: {credentials}\n"
                  f"  session: {session}\n")
        return tobiko.check_valid_type(session, KeystoneSessionFixture)

    @staticmethod
    def init_session(credentials: _credentials.KeystoneCredentials) \
            -> KeystoneSessionFixture:
        return KeystoneSessionFixture(credentials=credentials)


KEYSTONE_SESSION_MANAGER = KeystoneSessionManager()


def default_keystone_session(
        shared: bool = True,
        init_session: InitSessionType = None,
        manager: KeystoneSessionManager = None) -> \
        KeystoneSession:
    return get_keystone_session(shared=shared,
                                init_session=init_session,
                                manager=manager)


def get_keystone_session(
        credentials: _credentials.KeystoneCredentialsType = None,
        shared: bool = True,
        init_session: typing.Any = None,
        manager: KeystoneSessionManager = None) -> \
        KeystoneSession:
    if manager is None:
        manager = KEYSTONE_SESSION_MANAGER
    session = manager.get_session(credentials=credentials,
                                  shared=shared,
                                  init_session=init_session)
    tobiko.check_valid_type(session, KeystoneSessionFixture)
    return tobiko.setup_fixture(session).session


def get_keystone_endpoint(
        session: KeystoneSessionType = None,
        auth: typing.Optional[_plugin.BaseAuthPlugin] = None,
        **kwargs) -> \
        typing.Optional[str]:
    return keystone_session(session).get_endpoint(auth=auth, **kwargs)


def get_keystone_token(
        session: KeystoneSessionType = None,
        auth: typing.Optional[_plugin.BaseAuthPlugin] = None) -> \
        typing.Optional[str]:
    return keystone_session(session).get_token(auth=auth)
