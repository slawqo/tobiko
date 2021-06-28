# Copyright (c) 2021 Red Hat, Inc.
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

import typing

import netaddr
import testtools

import tobiko
from tobiko.shell import curl
from tobiko.shell import ssh
from tobiko.openstack import keystone
from tobiko.openstack import stacks


@keystone.skip_unless_has_keystone_credentials()
class TestCurl(testtools.TestCase):

    stack = tobiko.required_setup_fixture(stacks.UbuntuServerStackFixture)

    def test_execute_curl(
            self,
            ip_address: typing.Optional[netaddr.IPAddress] = None,
            ssh_client: typing.Optional[ssh.SSHClientFixture] = None):
        if ip_address is None:
            # Use the floating IP
            ip_address = self.stack.ip_address
        http_port = self.stack.http_port
        result = curl.execute_curl(scheme='http',
                                   hostname=ip_address,
                                   port=http_port,
                                   path='/id',
                                   ssh_client=ssh_client,
                                   connect_timeout=10.,
                                   retry_count=30,
                                   retry_timeout=300.,
                                   retry_interval=10.).strip()
        self.assertEqual(self.stack.server_name, result)

    def test_execute_curl_ipv4(self):
        self.test_execute_curl(ip_address=self.get_fixed_ip(ip_version=4),
                               ssh_client=self.stack.ssh_client)

    def test_execute_curl_ipv6(self):
        self.test_execute_curl(ip_address=self.get_fixed_ip(ip_version=6),
                               ssh_client=self.stack.ssh_client)

    def get_fixed_ip(self, ip_version):
        for fixed_ip in self.stack.fixed_ips:
            ip_address = netaddr.IPAddress(fixed_ip['ip_address'])
            if ip_version == ip_address.version:
                return ip_address
        self.skipTest(f"Server {self.stack.server_id} has any "
                      f"IPv{ip_version} address.")
