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

import functools

from oslo_log import log
import requests

import tobiko
from tobiko import config
from tobiko.openstack import glance
from tobiko.openstack.stacks import _centos

LOG = log.getLogger(__name__)
CONF = config.CONF

RHEL_IMAGE_MAJOR_VERSION = '8.4'
RHEL_IMAGE_MINOR_VERSION = '1254'

RHEL_IMAGE_URL = ('http://download.devel.redhat.com/brewroot/packages/'
                  f'rhel-guest-image/{RHEL_IMAGE_MAJOR_VERSION}/'
                  f'{RHEL_IMAGE_MINOR_VERSION}/images/'
                  f'rhel-guest-image-{RHEL_IMAGE_MAJOR_VERSION}-'
                  f'{RHEL_IMAGE_MINOR_VERSION}.x86_64.qcow2')


def skip_unless_has_rhel_image():
    return tobiko.skip_unless('RHEL image not found',
                              has_rhel_image)


@functools.lru_cache()
def has_rhel_image() -> bool:
    image_url = tobiko.get_fixture(RhelImageFixture).image_url
    try:
        response = requests.get(image_url, stream=True)
    except requests.exceptions.ConnectionError as ex:
        LOG.debug(f'RHEL image file not found at {image_url}: {ex}',
                  exc_info=1)
        return False

    if response.status_code == 404:
        LOG.debug(f'RHEL image file not found at {image_url}')
        return False

    response.raise_for_status()
    LOG.debug(f'RHEL image file found at {image_url}')
    return True


@skip_unless_has_rhel_image()
class RhelImageFixture(glance.URLGlanceImageFixture):

    image_url = CONF.tobiko.rhel.image_url or RHEL_IMAGE_URL
    image_name = CONF.tobiko.rhel.image_name
    image_file = CONF.tobiko.rhel.image_file
    disk_format = CONF.tobiko.rhel.disk_format or "qcow2"
    container_format = CONF.tobiko.rhel.container_format or "bare"
    username = CONF.tobiko.rhel.username or 'cloud-user'
    password = CONF.tobiko.rhel.password
    connection_timeout = CONF.tobiko.rhel.connection_timeout
    disabled_algorithms = CONF.tobiko.rhel.disabled_algorithms


class RedHatFlavorStackFixture(_centos.CentosFlavorStackFixture):
    pass


class RedHatServerStackFixture(_centos.CentosServerStackFixture):

    #: Glance image used to create a Nova server instance
    # (alternative is given for cases the RHEL image is failed to be
    # set up)
    image_fixture = tobiko.required_fixture(RhelImageFixture)

    #: Flavor used to create a Nova server instance
    flavor_stack = tobiko.required_fixture(RedHatFlavorStackFixture)
