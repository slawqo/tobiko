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

from oslo_config import cfg


def register_tobiko_options(conf):
    conf.register_opts(
        group=cfg.OptGroup('paramiko'),
        opts=[cfg.StrOpt('config_file',
                         default='~/.ssh/config',
                         help="Default user SSH configuration file"),
              cfg.StrOpt('key_file',
                         default='~/.ssh/id_rsa',
                         help="Default SSH private key file"),
              cfg.IntOpt('connect_timeout',
                         default=120,
                         help="SSH connect timeout in seconds"),
              cfg.IntOpt('connect_sleep_time',
                         default=1,
                         help=("Seconds to wait after every failed SSH "
                               "connection attempt")),
              cfg.IntOpt('connect_sleep_time_increment',
                         default=1,
                         help=("Incremental seconds to wait after every "
                               "failed SSH connection attempt")),
              cfg.StrOpt('proxy_jump',
                         default=None,
                         help="Default SSH proxy server"),
              cfg.StrOpt('proxy_command',
                         default=None,
                         help="Default proxy command"),
              ])
