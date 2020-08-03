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

import six

from tobiko import config
from tobiko.tests import unit


CONF = config.CONF
TIPLEO_CONF = CONF.tobiko.tripleo


class TripleoConfigTest(unit.TobikoUnitTest):

    def test_ssh_key_filename(self):
        self.assertIsInstance(TIPLEO_CONF.undercloud_ssh_key_filename,
                              six.string_types)


class UndercloudConfigTest(unit.TobikoUnitTest):

    def test_undercloud_ssh_hostname(self):
        value = TIPLEO_CONF.undercloud_ssh_hostname
        if value is not None:
            self.assertIsInstance(value, six.string_types)

    def test_undercloud_ssh_port(self):
        value = TIPLEO_CONF.undercloud_ssh_port
        if value is not None:
            self.assertIsInstance(value, int)
            self.assertIn(value, six.moves.range(1, 2 ** 16))

    def test_undercloud_ssh_username(self):
        self.assertIsInstance(TIPLEO_CONF.undercloud_ssh_username,
                              six.string_types)

    def test_undercloud_rcfile(self):
        for rcfile in TIPLEO_CONF.undercloud_rcfile:
            self.assertIsInstance(rcfile, six.string_types)


class OvercloudConfigTest(unit.TobikoUnitTest):

    def test_overcloud_ssh_port(self):
        value = TIPLEO_CONF.overcloud_ssh_port
        if value is not None:
            self.assertIsInstance(value, int)
            self.assertIn(value, six.moves.range(1, 2 ** 16))

    def test_overcloud_ssh_username(self):
        self.assertIsInstance(TIPLEO_CONF.overcloud_ssh_username,
                              six.string_types)

    def test_overcloud_rcfile(self):
        for rcfile in TIPLEO_CONF.overcloud_rcfile:
            self.assertIsInstance(rcfile, six.string_types)
