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

from tobiko.config import CONF
from tobiko.openstack import keystone
from tobiko.tests import unit


DEFAULT_CREDENTIALS = keystone.keystone_credentials(
    auth_url='http://127.0.0.1:5000/identiy/v3',
    username='default',
    project_name='default',
    password='this is a secret')


class OpenstackTest(unit.TobikoUnitTest):

    def setUp(self):
        super(OpenstackTest, self).setUp()
        self.patch_object(CONF.tobiko, 'keystone', DEFAULT_CREDENTIALS)
