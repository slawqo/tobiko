# Copyright 2022 Red Hat
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


GROUP_NAME = 'shiftstack'
OPTIONS = [
    # ShiftStack options
    cfg.StrOpt('local_clouds_file_path',
               default='.tobiko/shifstack/clouds.yaml',
               help="local clouds file path"),
    cfg.StrOpt('remote_clouds_file_path',
               default='~/clouds.yaml',
               help="remote clouds file path on undercloud-0 host"),
    cfg.StrOpt('cloud_name',
               default='shiftstack',
               help="Keystone credentials cloud name"),
    cfg.ListOpt('rcfile',
                default=['./shiftstackrc'],
                help="Path to the RC file used to populate OS_* environment "
                     "variables")
]


def register_tobiko_options(conf):
    conf.register_opts(group=cfg.OptGroup(GROUP_NAME), opts=OPTIONS)


def list_options():
    return [(GROUP_NAME, itertools.chain(OPTIONS))]
