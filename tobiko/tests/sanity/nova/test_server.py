# Copyright (c) 2022 Red Hat
# All Rights Reserved.
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
import pytest
import testtools

import tobiko
from tobiko import config
from tobiko.openstack import heat
from tobiko.openstack import nova
from tobiko.openstack import stacks


LOG = log.getLogger(__name__)


class CrateDeleteServerStackFixture(stacks.CirrosServerStackFixture):
    """Nova server for testing server deletion and creation
    """


@pytest.mark.minimal
@config.skip_if_prevent_create()
class CrateDeleteServerStackTest(testtools.TestCase):

    stack = tobiko.required_fixture(CrateDeleteServerStackFixture,
                                    setup=False)

    @classmethod
    def tearDownClass(cls) -> None:
        tobiko.cleanup_fixture(cls.stack.fixture)

    def test_1_create_server(self):
        """Test Nova server creation
        """
        tobiko.cleanup_fixture(self.stack)
        self.ensure_server()
        self.stack.assert_is_reachable()

    def test_2_delete_server(self):
        server = self.ensure_server(status='ACTIVE')
        self.stack.assert_is_reachable()

        nova.delete_server(server.id)
        for _ in tobiko.retry(timeout=60., interval=3.):
            try:
                server = nova.get_server(server_id=server.id)
            except nova.ServerNotFoundError:
                LOG.debug(f"Server '{server.id}' deleted")
                break
            else:
                LOG.debug(f"Waiting for server deletion:\n"
                          f" - server.id='{server.id}'"
                          f" - server.status='{server.status}'")
        self.stack.assert_is_unreachable()

    def ensure_server(self, status='ACTIVE'):
        try:
            server_id: str = self.stack.server_id
            nova.get_server(server_id=server_id)
        except heat.HeatStackNotFound:
            tobiko.setup_fixture(self.stack)
        except nova.ServerNotFoundError:
            tobiko.reset_fixture(self.stack)
        return self.stack.ensure_server_status(status=status)
