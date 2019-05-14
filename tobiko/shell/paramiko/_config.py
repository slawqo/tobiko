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

    _config_file = None
    config = None

    def __init__(self, config_file=None):
        super(SSHConfigFixture, self).__init__()
        if config_file:
            self._config_file = config_file

    def setup_fixture(self):
        self.setup_ssh_config()

    def setup_ssh_config(self):
        self.config = paramiko.SSHConfig()
        config_file = self.config_file
        if config_file:
            LOG.debug("Loading %r config file...", config_file)
            config_file = os.path.expanduser(config_file)
            if os.path.exists(config_file):
                with open(config_file) as f:
                    self.config.parse(f)
                LOG.debug("File %r parsed.", config_file)

    @property
    def config_file(self):
        return self._config_file or self.paramiko_conf.config_file

    def lookup(self, host):
        host_config = SSHHostConfig(host=host,
                                    ssh_config=self,
                                    host_config=self.config.lookup(host))
        LOG.debug('Lookup SSH config for for host %r:\n%r', host, host_config)
        return host_config

    def __repr__(self):
        return "{class_name!s}(config_file={config_file!r})".format(
            class_name=type(self).__name__, config_file=self.config_file)


class SSHHostConfig(collections.namedtuple('SSHHostConfig', ['host',
                                                             'ssh_config',
                                                             'host_config'])):

    paramiko_conf = tobiko.required_setup_fixture(SSHParamikoConfFixture)

    @property
    def username(self):
        return self.host_config.get('user')

    @property
    def hostname(self):
        return self.host_config.get('hostname', self.host)

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
        return self.host_config.get('proxycommand',
                                    self.paramiko_conf.proxy_command)

    def __getattr__(self, name):
        try:
            return self.host_config[name]
        except KeyError:
            pass
        message = "{!r} object has no attribute {!r}".format(self, name)
        raise AttributeError(message)
