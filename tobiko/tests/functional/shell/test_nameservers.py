# Copyright (c) 2019 Red Hat, Inc.
#
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

import testtools

from tobiko.shell import sh


class NameserversTest(testtools.TestCase):

    ssh_client = None

    def test_list_nameservers(self):
        nameservers = sh.list_nameservers(ssh_client=self.ssh_client)
        self.assertNotEqual([], nameservers)
        return nameservers

    def test_list_nameservers_with_ip_version_4(self):
        nameservers = sh.list_nameservers(ssh_client=self.ssh_client,
                                          ip_version=4)
        for nameserver in nameservers:
            self.assertEqual(4, nameserver.version, nameserver)

    def test_list_nameservers_with_ip_version_6(self):
        nameservers = sh.list_nameservers(ssh_client=self.ssh_client,
                                          ip_version=6)
        for nameserver in nameservers:
            self.assertEqual(6, nameserver.version, nameserver)
