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

CENTOS_IMAGE_URL = (
    'https://cloud.centos.org/centos/8/x86_64/images/'
    'CentOS-8-GenericCloud-8.4.2105-20210603.0.x86_64.qcow2')


class CentosImageFixture(glance.URLGlanceImageFixture):
    image_url = CONF.tobiko.centos.image_url or CENTOS_IMAGE_URL
    image_name = CONF.tobiko.centos.image_name
    image_file = CONF.tobiko.centos.image_file
    disk_format = CONF.tobiko.centos.disk_format or "qcow2"
    container_format = CONF.tobiko.centos.container_format or "bare"
    username = CONF.tobiko.centos.username or 'centos'
    password = CONF.tobiko.centos.password
    connection_timeout = CONF.tobiko.centos.connection_timeout or 800.


CENTOS7_IMAGE_URL = (
    'https://cloud.centos.org/centos/7/images/'
    'CentOS-7-x86_64-GenericCloud.qcow2.xz')


class Centos7ImageFixture(glance.URLGlanceImageFixture):
    image_url = CONF.tobiko.centos7.image_url or CENTOS7_IMAGE_URL
    image_name = CONF.tobiko.centos7.image_name
    image_file = CONF.tobiko.centos7.image_file
    disk_format = CONF.tobiko.centos7.disk_format or "qcow2"
    container_format = CONF.tobiko.centos7.container_format or "bare"
    username = CONF.tobiko.centos7.username or 'centos'
    password = CONF.tobiko.centos7.password
    connection_timeout = CONF.tobiko.centos7.connection_timeout or 800.


class CentosFlavorStackFixture(_nova.FlavorStackFixture):
    ram = 512
    swap = 1024


class CentosServerStackFixture(_nova.CloudInitServerStackFixture):

    #: Glance image used to create a Nova server instance
    image_fixture = tobiko.required_setup_fixture(CentosImageFixture)

    #: Flavor used to create a Nova server instance
    flavor_stack = tobiko.required_setup_fixture(CentosFlavorStackFixture)


class Centos7ServerStackFixture(CentosServerStackFixture):

    #: Glance image used to create a Nova server instance
    image_fixture = tobiko.required_setup_fixture(Centos7ImageFixture)
