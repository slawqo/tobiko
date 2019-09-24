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

import os
import itertools

from oslo_config import cfg


OS_FAULTS_SERVICES = ['openvswitch',
                      'tripleo_cinder_api',
                      'tripleo_cinder_api_cron',
                      'tripleo_cinder_scheduler',
                      'tripleo_clustercheck',
                      'tripleo_glance_api',
                      'tripleo_horizon']

OS_FAULTS_CONTAINERS = ['neutron_ovs_agent',
                        'neutron_metadata_agent',
                        'neutron_api']

OS_FAULTS_CONFIG_DIRNAMES = ['.',
                             '~/.config/os-faults',
                             '/etc/openstack']

OS_FAULTS_CONFIG_FILENAMES = ['os-faults.json',
                              'os-faults.yaml',
                              'os-faults.yml']

OS_FAULTS_TEMPLATE_DIRNAMES = ['.',
                               os.path.join(os.path.dirname(__file__),
                                            'templates')]

OS_FAULTS_GENERATE_CONFIG_DIRNAME = '~/.tobiko/os-faults'


GROUP_NAME = 'os_faults'
OPTIONS = [
    cfg.ListOpt('config_dirnames',
                default=OS_FAULTS_CONFIG_DIRNAMES,
                help="Directories where to look for os-faults config file"),
    cfg.ListOpt('config_filenames',
                default=OS_FAULTS_CONFIG_FILENAMES,
                help="Base file names used to look for os-faults config file"),
    cfg.ListOpt('template_dirnames',
                default=OS_FAULTS_TEMPLATE_DIRNAMES,
                help=("location where to look for a template file to be used "
                      "to generate os-faults config file")),
    cfg.StrOpt('generate_config_dirname',
               default=OS_FAULTS_GENERATE_CONFIG_DIRNAME,
               help=("location where to generate config file from template")),
    cfg.ListOpt('services',
                default=OS_FAULTS_SERVICES,
                help="List of services to be handler with os-faults"),
    cfg.ListOpt('containers',
                default=OS_FAULTS_CONTAINERS,
                help="List of containers to be handler with os-faults"),
    cfg.ListOpt('nodes',
                default=None,
                help="List of cloud nodes to be handled with os-faults")
    ]


def register_tobiko_options(conf):
    conf.register_opts(group=cfg.OptGroup(GROUP_NAME), opts=OPTIONS)


def list_options():
    return [(GROUP_NAME, itertools.chain(OPTIONS))]
