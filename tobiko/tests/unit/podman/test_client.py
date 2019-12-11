# Copyright 2018 Red Hat
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

import mock
import six

# We need to ignore this code under py2
# it's not compatible and parser will failed even if we use
# the `unittest.skipIf` decorator, because during the test discovery
# stestr and unittest will load this test
# module before running it and it will load podman
# too which isn't compatible in version leather than python 3
# Also the varlink mock module isn't compatible with py27, is using
# annotations syntaxe to generate varlink interface for the mocked service
# and it will raise related exceptions too.
# For all these reasons we can't run podman tests under a python 2 environment
if six.PY3:
    from tobiko import podman
    from tobiko.tests import unit

    from varlink import mock as varlink_mock

    class TestPodmanClient(unit.TobikoUnitTest):

        @varlink_mock.mockedservice(
            fake_service=unit.mocked_service.ServicePod,
            fake_types=unit.mocked_service.types,
            name='io.podman',
            address='unix:@podmantests'
        )
        @mock.patch(
            'tobiko.podman._client.PodmanClientFixture.discover_podman_socket'
        )
        def test_init(self, mocked_discover_podman_socket):
            mocked_discover_podman_socket.return_value = 'unix:@podmantests'
            client = podman.get_podman_client().connect()
            pods = client.pods.get('135d71b9495f')
            self.assertEqual(pods["numberofcontainers"], "2")
