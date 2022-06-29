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

from oslo_log import log

import tobiko
from tobiko.shiftstack import _keystone


LOG = log.getLogger(__name__)


class HasShiftstackFixture(tobiko.SharedFixture):

    def __init__(self,
                 has_shiftstack: bool = None):
        # pylint: disable=redefined-outer-name
        super(HasShiftstackFixture, self).__init__()
        self.has_shiftstack = has_shiftstack

    def setup_fixture(self):
        if self.has_shiftstack is None:
            try:
                _keystone.shiftstack_keystone_session()
            except Exception:
                LOG.debug('Shifstack credentials not found', exc_info=1)
                self.has_shiftstack = False
            else:
                LOG.debug('Shifstack credentials was found')
                self.has_shiftstack = True


def has_shiftstack() -> bool:
    return tobiko.setup_fixture(HasShiftstackFixture).has_shiftstack


def skip_unless_has_shiftstack():
    return tobiko.skip_unless("Shifstack credentials not found",
                              predicate=has_shiftstack)
