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

import testtools
import yaml

from tobiko.openstack import nova


class TestUserData(testtools.TestCase):

    def test_user_data(self):
        self.assertEqual('', nova.user_data())

    def test_user_data_with_packages(self):
        user_data = nova.user_data({'packages': [1, 2]}, packages=[2, 3])
        self.assert_equal_cloud_config({"packages": [1, 2, 3]},
                                       user_data)

    def test_user_data_with_runcmd(self):
        user_data = nova.user_data({'runcmd': [["echo", 1]]},
                                   runcmd=['echo 2'])
        self.assert_equal_cloud_config({'runcmd': [['echo', '1'],
                                                   ['echo', '2']]},
                                       user_data)

    def assert_equal_cloud_config(self, expected, actual):
        self.assertTrue(actual.startswith('#cloud-config'))
        self.assertEqual(expected, yaml.load(actual))


class TestCloudConfig(testtools.TestCase):

    def test_cloud_config(self):
        self.assertEqual({}, nova.cloud_config())

    def test_cloud_config_with_packages(self):
        cloud_config = nova.cloud_config({'packages': [1, 2]}, packages=[2, 3])
        self.assertEqual({"packages": [1, 2, 3]}, cloud_config)

    def test_cloud_config_with_runcmd(self):
        cloud_config = nova.cloud_config({'runcmd': [["echo", 1]]},
                                         runcmd=['echo 2'])
        self.assertEqual({'runcmd': [['echo', '1'],
                                     ['echo', '2']]},
                         cloud_config)
