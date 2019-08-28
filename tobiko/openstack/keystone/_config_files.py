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

import appdirs


APPDIRS = appdirs.AppDirs('openstack', 'OpenStack', multipath='/etc')
CONFIG_HOME = APPDIRS.user_config_dir
CACHE_PATH = APPDIRS.user_cache_dir

UNIX_CONFIG_HOME = os.path.join(
    os.path.expanduser(os.path.join('~', '.config')), 'openstack')
UNIX_SITE_CONFIG_HOME = '/etc/openstack'

SITE_CONFIG_HOME = APPDIRS.site_config_dir

CONFIG_SEARCH_PATH = [
    os.getcwd(),
    CONFIG_HOME, UNIX_CONFIG_HOME,
    SITE_CONFIG_HOME, UNIX_SITE_CONFIG_HOME
]
YAML_SUFFIXES = ('.yaml', '.yml')
JSON_SUFFIXES = ('.json',)


def get_cloud_config_files():
    return [
        os.path.join(d, 'clouds' + s)
        for d in CONFIG_SEARCH_PATH
        for s in YAML_SUFFIXES + JSON_SUFFIXES]
