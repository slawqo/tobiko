# Copyright (c) 2019 Red Hat
# All Rights Reserved.
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

from keystoneclient import discover
from keystoneclient.v3 import Client
from oslo_log import log
import mock

from tobiko.openstack import keystone
from tobiko.tests import unit

LOG = log.getLogger(__name__)


class KeystoneDiscoverMock(object):

    def __init__(self, session, **kwargs):
        self.session = session
        self.kwargs = kwargs

    def create_client(self, version, unstable):
        LOG.debug("Create a mock keystone client for version {!r} "
                  "(unestable = {!r})", version, unstable)
        return Client(session=self.session)


class OpenstackTest(unit.TobikoUnitTest):

    default_keystone_credentials = keystone.keystone_credentials(
        auth_url='http://127.0.0.1:5000/v3',
        username='default',
        project_name='default',
        password='this is a secret')

    def setUp(self):
        super(OpenstackTest, self).setUp()
        from tobiko import config

        self.patch(config.CONF.tobiko, 'keystone',
                   self.default_keystone_credentials)
        self.patch(discover, 'Discover', KeystoneDiscoverMock)

    def patch_get_heat_client(self, *args, **kwargs):
        from heatclient import client
        from tobiko.openstack import heat
        from tobiko.openstack.heat import _client

        kwargs.setdefault('return_value', mock.MagicMock(specs=client.Client))
        get_heat_client = self.patch(_client, 'get_heat_client', *args,
                                     **kwargs)
        self.patch(heat, 'get_heat_client', get_heat_client)
        return get_heat_client

    def patch_get_neutron_client(self, *args, **kwargs):
        from neutronclient.v2_0 import client
        from tobiko.openstack import neutron
        from tobiko.openstack.neutron import _client

        kwargs.setdefault('return_value', mock.MagicMock(specs=client.Client))
        get_neutron_client = self.patch(_client, 'get_neutron_client', *args,
                                        **kwargs)
        self.patch(neutron, 'get_neutron_client', get_neutron_client)
        return get_neutron_client
