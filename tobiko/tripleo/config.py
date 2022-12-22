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

from oslo_config import cfg


GROUP_NAME = 'tripleo'
OPTIONS = [
    # Undercloud options
    cfg.StrOpt('undercloud_ssh_hostname',
               default='undercloud-0',
               help="hostname or IP address to be used to connect to "
                    "undercloud host"),
    cfg.IntOpt('undercloud_ssh_port',
               default=None,
               help="TCP port of SSH server on undercloud host"),
    cfg.StrOpt('undercloud_ssh_username',
               default='stack',
               help="Username with access to stackrc and overcloudrc files"),
    cfg.StrOpt('undercloud_ssh_key_filename',
               default=None,
               help="SSH key filename used to login to Undercloud node"),
    cfg.ListOpt('undercloud_rcfile',
                default=['~/stackrc'],
                help="Undercloud RC filename"),
    cfg.StrOpt('undercloud_cloud_name',
               default='undercloud',
               help='undercloud cloud name to be used for loading credentials '
                    'from the undercloud clouds files'),


    # Overcloud options
    cfg.IntOpt('overcloud_ssh_port',
               default=None,
               help="TCP port of SSH server on overcloud hosts"),
    cfg.StrOpt('overcloud_ssh_username',
               default='heat-admin',
               help="Default username used to connect to overcloud nodes"),
    cfg.StrOpt('overcloud_ssh_key_filename',
               default='~/.ssh/id_overcloud',
               help="SSH key filename used to login to Overcloud nodes"),
    cfg.ListOpt('overcloud_rcfile',
                default=['~/overcloudrc', '~/qe-Cloud-0rc'],
                help="Overcloud RC filenames"),
    cfg.StrOpt('overcloud_cloud_name',
               default='overcloud',
               help='overcloud cloud name to be used for loading credentials '
                    'from the overcloud clouds files'),
    cfg.IntOpt('overcloud_ip_version',
               help=("Default IP address version to be used to connect to "
                     "overcloud nodes ")),
    cfg.StrOpt('overcloud_network_name',
               help="Name of network used to connect to overcloud nodes"),
    cfg.DictOpt('overcloud_groups_dict',
                help='Dictionary with the node groups corresponding to '
                     'different hostname prefixes',
                default={'ctrl': 'controller', 'cmp': 'compute'}),

    # Other options
    cfg.StrOpt('inventory_file',
               default='.ansible/inventory/tripleo.yaml',
               help="path to where to export tripleo inventory file"),

    cfg.BoolOpt('has_external_load_balancer',
                default=False,
                help="OSP env was done with an external load balancer"),

    cfg.BoolOpt('ceph_rgw',
                default=False,
                help="whether Ceph RGW is deployed"),
]


def register_tobiko_options(conf):
    conf.register_opts(group=cfg.OptGroup(GROUP_NAME), opts=OPTIONS)


def list_options():
    return [(GROUP_NAME, itertools.chain(OPTIONS))]


def setup_tobiko_config(conf):
    # pylint: disable=unused-argument
    from tobiko.tripleo import _ansible
    from tobiko.tripleo import overcloud
    from tobiko.tripleo import topology

    _ansible.setup_undercloud_ansible_playbook()
    overcloud.setup_overcloud_keystone_credentials()
    topology.setup_tripleo_topology()
