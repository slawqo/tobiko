# Copyright 2018 Red Hat
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
        group=cfg.OptGroup('identity'),
        opts=[cfg.StrOpt('http_proxy',
                         help="HTTP proxy URL for Rest APIs"),
              cfg.IntOpt('api_version',
                         help="Identity API version"),
              cfg.StrOpt('auth_url',
                         help="Identity service URL"),
              cfg.StrOpt('username',
                         help="Username"),
              cfg.StrOpt('password',
                         help="Password"),
              cfg.StrOpt('project_name',
                         help="Project name"),
              cfg.StrOpt('user_domain_name',
                         help="User domain name"),
              cfg.StrOpt('project_domain_name',
                         help="Project domain name")])

    conf.register_opts(
        group=cfg.OptGroup('compute'),
        opts=[cfg.StrOpt('image_ref',
                         help="Default image reference"),
              cfg.StrOpt('flavor_ref',
                         help="Default flavor reference")])

    conf.register_opts(
        group=cfg.OptGroup('network'),
        opts=[cfg.StrOpt('floating_network_name',
                         help="Network name for creating floating IPs")])

    conf.register_opts(
        group=cfg.OptGroup('shell'),
        opts=[cfg.StrOpt('command',
                         help="Default shell command used for executing "
                              "local commands")])


def setup_tobiko_config():
    pass
