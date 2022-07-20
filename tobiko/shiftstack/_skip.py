# Copyright 2022 Red Hat
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

import tobiko
from tobiko.openstack import keystone
from tobiko.shiftstack import _keystone
from tobiko import tripleo

LOG = log.getLogger(__name__)


def check_shiftstack():
    try:
        tripleo.check_overcloud()
    except tripleo.OvercloudNotFound as ex:
        raise ShiftstackNotFound(
            reason=f'Overcloud not found ({ex})') from ex

    try:
        _keystone.shiftstack_keystone_session()
    except keystone.NoSuchKeystoneCredentials as ex:
        raise ShiftstackNotFound(
            reason=f'Keystone credentials not found ({ex})') from ex


class ShiftstackNotFound(tobiko.ObjectNotFound):
    message = 'shiftstack not found: {reason}'


@functools.lru_cache()
def has_shiftstack() -> bool:
    try:
        check_shiftstack()
    except ShiftstackNotFound as ex:
        LOG.debug(f'Shiftstack not found: {ex}')
        return False
    else:
        LOG.debug('Shiftstack found')
        return True


def skip_unless_has_shiftstack():
    return tobiko.skip_unless("Shifstack credentials not found",
                              predicate=has_shiftstack)
