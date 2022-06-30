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

from unittest import mock

from tobiko.tests import unit
from tobiko.openstack import nova


class ServerTest(unit.TobikoUnitTest):

    def test_get_server_id_with_str(self):
        self.assertEqual('<server-id>',
                         nova.get_server_id('<server-id>'))

    def test_get_server_id_with_server(self):
        server_mock = mock.Mock(id='<server-id>')
        self.assertEqual('<server-id>',
                         nova.get_server_id(server_mock))
