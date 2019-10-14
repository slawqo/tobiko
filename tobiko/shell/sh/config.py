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

import itertools

from oslo_config import cfg

GROUP_NAME = 'shell'
OPTIONS = [
    cfg.StrOpt('command',
               default='/bin/sh -c',
               help="Default shell command used for executing "
                    "local commands"),
    cfg.StrOpt('sudo',
               default='sudo',
               help="Default sudo command used for executing "
                    "commands as superuser or another user")
]


def register_tobiko_options(conf):
    conf.register_opts(group=cfg.OptGroup('shell'), opts=OPTIONS)


def list_options():
    return [(GROUP_NAME, itertools.chain(OPTIONS))]
