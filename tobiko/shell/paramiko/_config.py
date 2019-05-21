# Copyright (c) 2019 Red Hat, Inc.
#
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

import collections
import os

from oslo_log import log
import paramiko

import tobiko


LOG = log.getLogger(__name__)


class SSHParamikoConfFixture(tobiko.SharedFixture):

    conf = None

    def setup_fixture(self):
        from tobiko import config
        CONF = config.CONF
        self.conf = CONF.tobiko.paramiko

    def __getattr__(self, name):
        return getattr(self.conf, name)


class SSHConfigFixture(tobiko.SharedFixture):

    paramiko_conf = tobiko.required_setup_fixture(SSHParamikoConfFixture)

    _config_files = None
    config = None

    def __init__(self, config_files=None):
        super(SSHConfigFixture, self).__init__()
        if config_files:
            self._config_files = tuple(config_files)

    def setup_fixture(self):
        self.setup_ssh_config()

    def setup_ssh_config(self):
        self.config = paramiko.SSHConfig()
        for config_file in self.config_files:
            config_file = os.path.expanduser(config_file)
            if os.path.exists(config_file):
                LOG.debug("Parsing %r config file...", config_file)
                with open(config_file) as f:
                    self.config.parse(f)
                LOG.debug("File %r parsed.", config_file)

    @property
    def config_files(self):
        return self._config_files or self.paramiko_conf.config_files

    def lookup(self, host):
        return SSHHostConfig(host=host,
                            ssh_config=self,
                            host_config=self.config.lookup(host))

    def __repr__(self):
        return "{class_name!s}(config_files={config_files!r})".format(
            class_name=type(self).__name__, config_files=self.config_files)


class SSHHostConfig(collections.namedtuple('SSHHostConfig', ['host',
                                                             'ssh_config',
                                                             'host_config'])):

    paramiko_conf = tobiko.required_setup_fixture(SSHParamikoConfFixture)

    @property
    def hostname(self):
        return self.host_config.get('hostname', self.host)

    @property
    def port(self):
        return self.host_config.get('port')

    @property
    def username(self):
        return self.host_config.get('user')

    @property
    def key_filename(self):
        return self.host_config.get('identityfile',
                                    self.paramiko_conf.key_file)

    @property
    def proxy_jump(self):
        proxy_jump = (self.host_config.get('proxyjump') or
                      self.paramiko_conf.proxy_jump)
        if not proxy_jump:
            return None

        proxy_hostname = self.ssh_config.lookup(proxy_jump).hostname
        if ({proxy_jump, proxy_hostname} & {self.host, self.hostname}):
            # Avoid recursive proxy jump definition
            return None

        return proxy_jump

    @property
    def proxy_command(self):
        return (self.host_config.get('proxycommand') or
                self.paramiko_conf.proxy_command)

    @property
    def allow_agent(self):
        return (is_yes(self.host_config.get('forwardagent')) or
                self.paramiko_conf.allow_agent)

    @property
    def compress(self):
        return (is_yes(self.host_config.get('compression')) or
                self.paramiko_conf.compress)

    @property
    def timeout(self):
        return (self.host_config.get('connetcttimeout') or
                self.paramiko_conf.timeout)

    @property
    def connect_parameters(self):
        return dict(hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_filename,
                    compress=self.compress,
                    timeout=self.timeout,
                    allow_agent=self.allow_agent)


def is_yes(value):
    return value and str(value).lower() == 'yes'
