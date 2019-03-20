# Copyright 2018 Red Hat
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

from tobiko.openstack import keystone
from tobiko.openstack import heat
from tobiko.openstack import neutron
from tobiko.openstack import nova


class ClientManager(object):
    """Manages OpenStack official Python clients."""

    _session = None
    _heat_client = None
    _neutron_client = None
    _nova_client = None

    def __init__(self, credentials=None):
        self.credentials = credentials

    @property
    def session(self):
        """Returns keystone session."""
        if self._session is None:
            self._session = keystone.get_keystone_session(
                credentials=self.credentials)
        return self._session

    @property
    def heat_client(self):
        if self._heat_client is None:
            self._heat_client = heat.get_heat_client(session=self.session)
        return self._heat_client

    @property
    def neutron_client(self):
        """Returns neutron client."""
        if self._neutron_client is None:
            self._neutron_client = neutron.get_neutron_client(
                session=self.session)
        return self._neutron_client

    @property
    def nova_client(self):
        """Returns nova client."""
        if self._nova_client is None:
            self._nova_client = nova.get_nova_client(session=self.session)
        return self._nova_client
