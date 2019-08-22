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

import tobiko
from tobiko import config
from tobiko.openstack import keystone
from tobiko.shell import ssh
from tobiko.shell import sh

CONF = config.CONF


def undercloud_ssh_client():
    host_config = undercloud_host_config()
    return ssh.ssh_client(host='undercloud-0', host_config=host_config)


def undercloud_host_config():
    return tobiko.setup_fixture(UndecloudHostConfig)


def fetch_os_env(rcfile):
    command = ". {rcfile}; env | grep '^OS_'".format(rcfile=rcfile)
    result = sh.execute(command, ssh_client=undercloud_ssh_client())
    env = {}
    for line in result.stdout.splitlines():
        name, value = line.split('=')
        env[name] = value
    return env


def load_undercloud_rcfile():
    return fetch_os_env(rcfile=CONF.tobiko.tripleo.undercloud_rcfile)


class UndercloudKeystoneCredentialsFixture(
        keystone.EnvironKeystoneCredentialsFixture):
    def get_environ(self):
        return load_undercloud_rcfile()


def has_undercloud():
    host_config = undercloud_host_config()
    return bool(host_config.hostname)


skip_if_missing_undercloud = tobiko.skip_unless(
    'TripleO undercloud hostname not configured', has_undercloud)


class UndecloudHostConfig(tobiko.SharedFixture):

    host = 'undercloud-0'
    hostname = None
    port = None
    username = None
    key_filename = None

    def setup_fixture(self):
        self.hostname = CONF.tobiko.tripleo.undercloud_ssh_hostname
        self.port = CONF.tobiko.tripleo.undercloud_ssh_port
        self.username = CONF.tobiko.tripleo.undercloud_ssh_username
        self.key_filename = CONF.tobiko.tripleo.ssh_key_filename
