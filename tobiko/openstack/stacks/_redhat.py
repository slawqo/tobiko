# Copyright 2020 Red Hat
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
from tobiko.openstack.stacks import _centos


CONF = config.CONF

RHEL_IMAGE_MAJOR_VERSION = '8.2'
RHEL_IMAGE_MINOR_VERSION = '501'

RHEL_IMAGE_URL = ('http://download.devel.redhat.com/brewroot/packages/'
                  f'rhel-guest-image/{RHEL_IMAGE_MAJOR_VERSION}/'
                  f'{RHEL_IMAGE_MINOR_VERSION}/images/'
                  f'rhel-guest-image-{RHEL_IMAGE_MAJOR_VERSION}-'
                  f'{RHEL_IMAGE_MINOR_VERSION}.x86_64.qcow2')


class RhelImageFixture(glance.URLGlanceImageFixture):

    image_url = CONF.tobiko.rhel.image_url or RHEL_IMAGE_URL
    image_name = CONF.tobiko.rhel.image_name
    image_file = CONF.tobiko.rhel.image_file
    disk_format = CONF.tobiko.rhel.disk_format or "qcow2"
    container_format = CONF.tobiko.rhel.container_format or "bare"
    username = CONF.tobiko.rhel.username or 'cloud-user'
    password = CONF.tobiko.rhel.password
    connection_timeout = CONF.tobiko.rhel.connection_timeout


class RedHatFlavorStackFixture(_centos.CentosFlavorStackFixture):
    pass


class RedHatServerStackFixture(_centos.CentosServerStackFixture):

    #: Glance image used to create a Nova server instance
    # (alternative is given for cases the RHEL image is failed to be
    # set up)
    image_fixture = tobiko.required_setup_fixture(
        RhelImageFixture, alternative=_centos.CentosImageFixture)

    #: Flavor used to create a Nova server instance
    flavor_stack = tobiko.required_setup_fixture(RedHatFlavorStackFixture)
