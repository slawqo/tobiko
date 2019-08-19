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

import testtools

from tobiko import config
from tobiko.shell import sh
from tobiko.tripleo import undercloud

CONF = config.CONF


@undercloud.skip_if_missing_undercloud
class UndercloudSshConnectionTest(testtools.TestCase):

    def setUp(self):
        super(UndercloudSshConnectionTest, self).setUp()
        self.ssh_client = undercloud.undercloud_ssh_client()

    def test_connect_to_undercloud(self):
        self.ssh_client.connect()

    def test_fetch_undercloud_credentials(self):
        env = undercloud.load_undercloud_rcfile()
        self._test_fetch_credentials(env=env)

    def test_fetch_overcloud_credentials(self):
        env = undercloud.load_overcloud_rcfile()
        self._test_fetch_credentials(env=env)

    def _test_fetch_credentials(self, env):

        self.assertTrue(env['OS_AUTH_URL'])
        self.assertTrue(env.get('OS_USERNAME') or env.get('OS_USER_ID'))
        self.assertTrue(env['OS_PASSWORD'])
        self.assertTrue(env.get('OS_TENANT_NAME') or
                        env.get('OS_PROJECT_NAME') or
                        env.get('OS_TENANT_ID') or
                        env.get('OS_PROJECT_ID'))

    def test_execute_command(self):
        result = sh.execute('hostname', ssh_client=self.ssh_client)
        self.assertTrue(result.stdout.startswith('undercloud-0'))
