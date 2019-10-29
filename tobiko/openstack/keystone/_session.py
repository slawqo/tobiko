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

from keystoneauth1 import loading
from keystoneauth1 import session as _session
from oslo_log import log

import tobiko
from tobiko.openstack.keystone import _credentials
from tobiko import http


LOG = log.getLogger(__name__)


def keystone_session(obj):
    if not obj:
        return default_keystone_session()
    if tobiko.is_fixture(obj):
        obj = tobiko.get_fixture(obj)
        if isinstance(obj, KeystoneSessionFixture):
            obj = tobiko.setup_fixture(obj).session
    if isinstance(obj, _session.Session):
        return obj
    raise TypeError("Can't get {!r} object from {!r}".format(
        _session.Session, obj))


class KeystoneSessionFixture(tobiko.SharedFixture):

    session = None
    credentials = None

    VALID_CREDENTIALS_TYPES = (_credentials.KeystoneCredentials,
                               _credentials.KeystoneCredentialsFixture,
                               type, str)

    def __init__(self, credentials=None, session=None):
        super(KeystoneSessionFixture, self).__init__()
        if credentials:
            tobiko.check_valid_type(credentials, *self.VALID_CREDENTIALS_TYPES)
            self.credentials = credentials
        if session:
            self.session = session

    def setup_fixture(self):
        self.setup_session()

    def setup_session(self):
        session = self.session
        if not session:
            credentials = _credentials.get_keystone_credentials(
                self.credentials)

            LOG.debug("Create Keystone session with credentials %r",
                      credentials)
            credentials.validate()
            loader = loading.get_plugin_loader('password')
            params = credentials.to_dict()
            # api version parameter is not accepted
            params.pop('api_version', None)
            auth = loader.load_from_options(**params)
            self.session = session = _session.Session(
                auth=auth, verify=False)
            http.setup_http_session(session)
            self.credentials = credentials


class KeystoneSessionManager(object):

    def __init__(self):
        self.sessions = {}

    def get_session(self, credentials=None, init_session=None, shared=True):
        if shared:
            shared_key, session = self.get_shared_session(credentials)
        else:
            shared_key = session = None
        return session or self.create_session(credentials=credentials,
                                              init_session=init_session,
                                              shared=shared,
                                              shared_key=shared_key)

    def get_shared_session(self, credentials):
        if tobiko.is_fixture(credentials):
            key = tobiko.get_fixture_name(credentials)
        else:
            key = credentials
        return key, self.sessions.get(key)

    def create_session(self, credentials=None, init_session=None, shared=True,
                       shared_key=None):
        init_session = init_session or KeystoneSessionFixture
        assert callable(init_session)
        LOG.debug('Initialize Keystone session: %r(credentials=%r)',
                  init_session, credentials)
        session = init_session(credentials=credentials)

        if shared:
            self.sessions[shared_key] = session
        return session


SESSIONS = KeystoneSessionManager()


def default_keystone_session(shared=True, init_session=None, manager=None):
    return get_keystone_session(shared=shared, init_session=init_session,
                                manager=manager)


def get_keystone_session(credentials=None, shared=True, init_session=None,
                         manager=None):
    manager = manager or SESSIONS
    session = manager.get_session(credentials=credentials, shared=shared,
                                  init_session=init_session)
    return tobiko.setup_fixture(session).session
