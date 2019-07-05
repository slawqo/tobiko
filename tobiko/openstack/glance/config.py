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


CIRROS_IMAGE_URL = \
    'http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img'


def register_tobiko_options(conf):
    conf.register_opts(
        group=cfg.OptGroup('glance'),
        opts=[cfg.StrOpt('image_dir',
                         default='~/.tobiko/cache/glance/images',
                         help=("Default directory where to look for image "
                               "files")), ])

    for name in ['CirrOS']:
        group_name = name.lower()
        conf.register_opts(
            group=cfg.OptGroup(group_name),
            opts=[cfg.StrOpt('image_name',
                             help="Default " + name + " image name"),
                  cfg.StrOpt('image_url',
                             help="Default " + name + " image URL"),
                  cfg.StrOpt('image_file',
                             help="Default " + name + " image filename"),
                  cfg.StrOpt('container_format',
                             help="Default " + name + " container format"),
                  cfg.StrOpt('disk_format',
                             help="Default " + name + " disk format"),
                  cfg.StrOpt('username',
                             help="Default " + name + " username"),
                  cfg.StrOpt('password',
                             help="Default " + name + " password"), ])
