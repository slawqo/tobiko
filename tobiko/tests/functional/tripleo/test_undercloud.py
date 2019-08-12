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

import tobiko
from tobiko import config
from tobiko.shell import sh
from tobiko.shell import ssh


CONF = config.CONF
TRIPLEO_CONF = CONF.tobiko.tripleo


@tobiko.skip_unless('Undercloud SSH hostname not defined',
                    TRIPLEO_CONF.undercloud_ssh_hostname,)
class UndercloudSshConnectionTest(testtools.TestCase):

    def setUp(self):
        super(UndercloudSshConnectionTest, self).setUp()
        self.ssh_client = ssh.ssh_client(
            host=TRIPLEO_CONF.undercloud_ssh_hostname,
            port=TRIPLEO_CONF.undercloud_ssh_port,
            username=TRIPLEO_CONF.undercloud_ssh_username)

    def test_connect_to_undercloud(self):
        self.ssh_client.connect()

    def test_fetch_undercloud_credentials(self):
        self._test_fetch_credentials(rcfile=TRIPLEO_CONF.undercloud_rcfile)

    def test_fetch_overcloud_credentials(self):
        self._test_fetch_credentials(rcfile=TRIPLEO_CONF.overcloud_rcfile)

    def _test_fetch_credentials(self, rcfile):
        env = self.fetch_os_env(rcfile=rcfile)
        self.assertTrue(env['OS_AUTH_URL'])
        self.assertTrue(env.get('OS_USERNAME') or env.get('OS_USER_ID'))
        self.assertTrue(env['OS_PASSWORD'])
        self.assertTrue(env.get('OS_TENANT_NAME') or
                        env.get('OS_PROJECT_NAME') or
                        env.get('OS_TENANT_ID') or
                        env.get('OS_PROJECT_ID'))

    def fetch_os_env(self, rcfile):
        command = ". {rcfile}; env | grep '^OS_'".format(rcfile=rcfile)
        result = sh.execute(command, ssh_client=self.ssh_client)
        env = {}
        for line in result.stdout.splitlines():
            name, value = line.split('=')
            env[name] = value
        return env
