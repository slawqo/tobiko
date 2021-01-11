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

import random
import typing

import netaddr
import testtools

import tobiko
from tobiko.shell import curl
from tobiko.shell import sh
from tobiko.shell import ssh
from tobiko.openstack import stacks


class TestCurl(testtools.TestCase):

    server_stack = tobiko.required_setup_fixture(
        stacks.CirrosServerStackFixture)

    def test_execute_curl(
            self,
            ip_address: typing.Optional[netaddr.IPAddress] = None,
            ssh_client: typing.Optional[ssh.SSHClientFixture] = None):
        if ip_address is None:
            # Use the floating IP
            ip_address = self.server_stack.ip_address
        server_id = self.server_stack.server_id
        http_port = random.randint(10000, 30000)
        reply = (f"HTTP/1.1 200 OK\r\n"
                 f"Content-Length:{len(server_id)}\r\n"
                 "\r\n"
                 f"{server_id}")
        http_server_command = f"nc -lk -p {http_port} -e echo -e '{reply}'"
        http_server = sh.process(http_server_command,
                                 ssh_client=self.server_stack.ssh_client)
        http_server.execute()
        self.addCleanup(http_server.kill)

        reply = curl.execute_curl(scheme='http',
                                  hostname=ip_address,
                                  port=http_port,
                                  ssh_client=ssh_client,
                                  connect_timeout=5.,
                                  retry_count=10,
                                  retry_timeout=60.)
        self.assertEqual(server_id, reply)

    def test_execute_curl_ipv4(self):
        self.test_execute_curl(ip_address=self.get_fixed_ip(ip_version=4),
                               ssh_client=self.server_stack.ssh_client)

    def test_execute_curl_ipv6(self):
        self.test_execute_curl(ip_address=self.get_fixed_ip(ip_version=6),
                               ssh_client=self.server_stack.ssh_client)

    def get_fixed_ip(self, ip_version):
        for fixed_ip in self.server_stack.fixed_ips:
            ip_address = netaddr.IPAddress(fixed_ip['ip_address'])
            if ip_version == ip_address.version:
                return ip_address
        self.skipTest(
            f"Server {self.server_stack.server_id} has any "
            f"IPv{ip_version} address.")
