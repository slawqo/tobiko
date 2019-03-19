# Copyright (c) 2018 Red Hat
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

import os.path

from tobiko.cmd import base
from tobiko.tests.unit import TobikoUnitTest
from tobiko.openstack import keystone


class TobikoCMDTest(TobikoUnitTest):

    command_name = None
    command_class = base.TobikoCMD

    default_credentials = keystone.keystone_credentials(
        api_version=3,
        auth_url='http://127.0.0.1:5000/identiy/v3',
        username='demo',
        project_name='demo',
        password='this is a secret',
        user_domain_name='Default',
        project_domain_name='Default')

    def setUp(self):
        TobikoUnitTest.setUp(self)
        self.patch('tobiko.config.CONF.tobiko.keystone',
                   self.default_credentials)

    def test_init(self, argv=None):
        self.patch_argv(argv=argv)
        cmd = self.command_class()
        self.assertIsNotNone(cmd.clientManager)
        self.assertTrue(os.path.isdir(cmd.templates_dir))
        self.assertIsNotNone(cmd.stackManager)
        return cmd

    def patch_argv(self, argv=None):
        return self.patch('sys.argv', [self.command_name] + (argv or []))
