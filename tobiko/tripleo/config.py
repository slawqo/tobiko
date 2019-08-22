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
    cfg.StrOpt('undercloud_ssh_hostname',
               default=None,
               help="hostname or IP address to be used to connect to "
                    "undercloud host"),
    cfg.IntOpt('undercloud_ssh_port',
               default=None,
               help="TCP port of SSH server on undercloud host"),
    cfg.StrOpt('undercloud_ssh_username',
               default='stack',
               help="Username with access to stackrc and overcloudrc files"),
    cfg.StrOpt('ssh_key_filename',
               default='~/.ssh/id_rsa',
               help="SSH key filename used to login to TripleO nodes"),
    cfg.StrOpt('undercloud_rcfile',
               default='~/stackrc',
               help="Undercloud RC filename"),
    cfg.StrOpt('overcloud_rcfile',
               default='~/overcloudrc',
               help="Overcloud RC filename")]


def register_tobiko_options(conf):
    conf.register_opts(group=cfg.OptGroup(GROUP_NAME), opts=OPTIONS)


def list_options():
    return [(GROUP_NAME, itertools.chain(OPTIONS))]


def setup_tobiko_config(conf):
    # pylint: disable=unused-argument
    from tobiko.openstack import keystone
    from tobiko.tripleo import overcloud
    if overcloud.has_overcloud():
        keystone.DEFAULT_KEYSTONE_CREDENTIALS_FIXTURES.append(
            overcloud.OvercloudKeystoneCredentialsFixture)
