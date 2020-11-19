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


class KeystoneSessionFixture(tobiko.SharedFixture):

    session: typing.Optional[_session.Session] = None
    credentials: _credentials.KeystoneCredentialsType = None

    VALID_CREDENTIALS_TYPES = (_credentials.KeystoneCredentials,
                               _credentials.KeystoneCredentialsFixture,
                               type, str)

    def __init__(self,
                 credentials: _credentials.KeystoneCredentialsType = None,
                 session: typing.Optional[_session.Session] = None):
        super(KeystoneSessionFixture, self).__init__()
        if credentials is not None:
            tobiko.check_valid_type(credentials, *self.VALID_CREDENTIALS_TYPES)
            self.credentials = credentials
        if session is not None:
            self.session = session

    def setup_fixture(self):
        self.setup_session()

    def setup_session(self):
        session = self.session
        if session is None:
            credentials = _credentials.get_keystone_credentials(
                self.credentials)

            LOG.debug("Create Keystone session from credentials "
                      f"{credentials}")
            credentials.validate()
            loader = loading.get_plugin_loader('password')
            params = credentials.to_dict()
            # api version parameter is not accepted
            params.pop('api_version', None)
            params.pop('cacert', None)
            auth = loader.load_from_options(**params)
            self.session = session = _session.Session(auth=auth, verify=False)
            http.setup_http_session(session)
            self.credentials = credentials


KeystoneSessionType = typing.Union[None,
                                   _session.Session,
                                   typing.Type,
                                   str,
                                   KeystoneSessionFixture]


def keystone_session(obj: KeystoneSessionType) -> _session.Session:
    if obj is None:
        return default_keystone_session()
    if tobiko.is_fixture(obj):
        obj = tobiko.get_fixture(obj)
        if isinstance(obj, KeystoneSessionFixture):
            obj = tobiko.setup_fixture(obj).session
    if isinstance(obj, _session.Session):
        return obj
    raise TypeError(f"Can't get {_session.Session} object from {obj}")


InitSessionType = typing.Optional[typing.Callable]


class KeystoneSessionManager(object):

    def __init__(self):
        self.sessions: typing.Dict[typing.Any,
                                   KeystoneSessionFixture] = {}

    def get_session(self,
                    credentials: typing.Any = None,
                    init_session: InitSessionType = None,
                    shared: bool = True) \
            -> KeystoneSessionFixture:
        if shared:
            shared_key, session = self.get_shared_session(credentials)
        else:
            shared_key = session = None
        if session is None:
            return self.create_session(credentials=credentials,
                                       init_session=init_session,
                                       shared=shared,
                                       shared_key=shared_key)
        else:
            return session

    def get_shared_session(self, credentials: typing.Any) \
            -> typing.Tuple[typing.Any,
                            typing.Optional[KeystoneSessionFixture]]:
        if tobiko.is_fixture(credentials):
            key = tobiko.get_fixture_name(credentials)
        else:
            key = credentials
        return key, self.sessions.get(key)

    def create_session(self,
                       credentials: typing.Any = None,
                       init_session: InitSessionType = None,
                       shared: bool = True,
                       shared_key: typing.Any = None) \
            -> KeystoneSessionFixture:
        if init_session is None:
            init_session = KeystoneSessionFixture
        assert callable(init_session)
        LOG.debug('Initialize Keystone session: %r(credentials=%r)',
                  init_session, credentials)
        session: KeystoneSessionFixture = init_session(
            credentials=credentials)
        tobiko.check_valid_type(session, KeystoneSessionFixture)
        if shared:
            self.sessions[shared_key] = session
        return session


SESSIONS = KeystoneSessionManager()


def default_keystone_session(
        shared: bool = True,
        init_session: InitSessionType = None,
        manager: typing.Optional[KeystoneSessionManager] = None) -> \
        _session.Session:
    return get_keystone_session(shared=shared, init_session=init_session,
                                manager=manager)


def get_keystone_session(
        credentials: typing.Any = None,
        shared: bool = True,
        init_session: typing.Any = None,
        manager: typing.Optional[KeystoneSessionManager] = None) -> \
        _session.Session:
    if manager is None:
        manager = SESSIONS
    session = manager.get_session(credentials=credentials, shared=shared,
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
