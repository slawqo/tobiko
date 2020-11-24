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

import tobiko
from tobiko import config
from tobiko.openstack import glance
from tobiko.openstack.stacks import _nova

CONF = config.CONF

UBUNTU_IMAGE_VERSION = 'focal'

UBUNTU_IMAGE_URL = (
    f'http://cloud-images.ubuntu.com/{UBUNTU_IMAGE_VERSION}/current/'
    f'{UBUNTU_IMAGE_VERSION}-server-cloudimg-amd64.img')


class UbuntuImageFixture(glance.URLGlanceImageFixture):
    image_url = CONF.tobiko.ubuntu.image_url or UBUNTU_IMAGE_URL
    image_name = CONF.tobiko.ubuntu.image_name
    image_file = CONF.tobiko.ubuntu.image_file
    disk_format = CONF.tobiko.ubuntu.disk_format or "qcow2"
    container_format = CONF.tobiko.ubuntu.container_format or "bare"
    username = CONF.tobiko.ubuntu.username or 'ubuntu'
    password = CONF.tobiko.ubuntu.password
    connection_timeout = CONF.tobiko.ubuntu.connection_timeout or 600.


class UbuntuFlavorStackFixture(_nova.FlavorStackFixture):
    ram = 256


class UbuntuServerStackFixture(_nova.ServerStackFixture):

    #: Glance image used to create a Nova server instance
    image_fixture = tobiko.required_setup_fixture(UbuntuImageFixture)

    #: Flavor used to create a Nova server instance
    flavor_stack = tobiko.required_setup_fixture(UbuntuFlavorStackFixture)

    #: Setup SWAP file in bytes
    swap_maxsize = 1 * 1024 * 1024 * 1024  # 1 GB
