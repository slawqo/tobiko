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

import itertools
import os

from oslo_config import cfg
from oslo_log import log

LOG = log.getLogger(__name__)

GROUP_NAME = 'ssh'
OPTIONS = [
    cfg.BoolOpt('debug',
                default=False,
                help=('Logout debugging messages of paramiko '
                      'library')),
    cfg.StrOpt('command',
               default='/usr/bin/ssh',
               help=('Default SSH client command')),
    cfg.StrOpt('port',
               default=None,
               help=('Default SSH port')),
    cfg.StrOpt('username',
               default=None,
               help=('Default SSH username')),
    cfg.ListOpt('config_files',
                default=['ssh_config'],
                help="Default user SSH configuration files"),
    cfg.ListOpt('key_file',
                default=['~/.ssh/id_rsa'],
                help="Default SSH private key file(s)"),
    cfg.BoolOpt('allow_agent',
                default=False,
                help=("Set to False to disable connecting to the "
                      "SSH agent")),
    cfg.BoolOpt('compress',
                default=False,
                help="Set to True to turn on compression"),
    cfg.FloatOpt('timeout',
                 default=15.,
                 help="SSH connect timeout in seconds"),
    cfg.IntOpt('connection_attempts',
               default=120,
               help=("Maximum number of connection attempts to be tried "
                     "before timeout")),
    cfg.FloatOpt('connection_interval',
                 default=5.,
                 help=("Minimal seconds to wait between every "
                       "failed SSH connection attempt")),
    cfg.IntOpt('connection_timeout',
               default=200.,
               help=("Time before stopping retrying establishing an SSH "
                     "connection")),
    cfg.StrOpt('proxy_jump',
               default=None,
               help="Default SSH proxy server"),
    cfg.StrOpt('proxy_command',
               default=None,
               help="Default proxy command"),
]


def register_tobiko_options(conf):
    conf.register_opts(group=cfg.OptGroup(GROUP_NAME), opts=OPTIONS)


def list_options():
    return [(GROUP_NAME, itertools.chain(OPTIONS))]


def setup_tobiko_config(conf):
    from tobiko.shell.ssh import _client
    from tobiko.shell.ssh import _ssh_key_file

    paramiko_logger = log.getLogger('paramiko')
    if conf.ssh.debug:
        if not paramiko_logger.isEnabledFor(log.DEBUG):
            # Print paramiko debugging messages
            paramiko_logger.logger.setLevel(log.DEBUG)
    else:
        if paramiko_logger.isEnabledFor(log.ERROR):
            # Silence paramiko debugging messages
            paramiko_logger.logger.setLevel(log.FATAL)

    ssh_proxy_client = _client.ssh_proxy_client()
    if ssh_proxy_client:
        key_file = _ssh_key_file.get_key_file(ssh_client=ssh_proxy_client)
        if key_file and os.path.isfile(key_file):
            LOG.info(f"Use SSH proxy server keyfile: {key_file}")
            conf.ssh.key_file.append(key_file)
