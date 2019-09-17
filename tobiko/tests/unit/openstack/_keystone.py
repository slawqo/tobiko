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

from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack import keystone
from tobiko.tests import unit


LOG = log.getLogger(__name__)


class DefaultKeystoneCredentialsPatch(unit.PatchFixture):

    credentials = keystone.keystone_credentials(
        auth_url='http://127.0.0.1:5000/v3',
        username='default',
        project_name='default',
        password='this is a secret')

    def __init__(self, credentials=None):
        if credentials:
            self.credentials = credentials
        tobiko.check_valid_type(self.credentials,
                                keystone.KeystoneCredentials)

    def setup_fixture(self):
        CONF = config.CONF
        keystone_conf = CONF.tobiko.keystone
        for key, value in self.credentials.to_dict().items():
            self.patch(keystone_conf, key, value)
