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

import abc

from oslo_log import log

import tobiko


LOG = log.getLogger(__name__)


class OpenstackClientFixture(tobiko.SharedFixture):

    client = None
    session = None

    def __init__(self, session=None, client=None):
        super(OpenstackClientFixture, self).__init__()
        if session:
            self.session = session
        if client:
            self.client = client

    def setup_fixture(self):
        self.setup_client()

    def setup_client(self):
        client = self.client
        if not client:
            self.session = session = self.get_session()
            self.client = client = self.init_client(session=session)
        return client

    def get_session(self):
        from tobiko.openstack import keystone
        return keystone.keystone_session(self.session)

    @abc.abstractmethod
    def init_client(self, session):
        raise NotImplementedError


class OpenstackClientManager(object):

    def __init__(self):
        self.clients = {}

    def get_client(self, session=None, shared=True, init_client=None):
        if shared:
            if session and tobiko.is_fixture(session):
                key = tobiko.get_fixture_name(session)
            else:
                key = session

            client = self.clients.get(key)
            if client:
                return client

        init_client = init_client or self.create_client
        assert callable(init_client)
        LOG.debug('Initialize OpenStack client: %r(session=%r)',
                  init_client, session)
        client = init_client(session=session)

        if shared:
            self.clients[key] = client
        return client

    def create_client(self, session):
        raise NotImplementedError
