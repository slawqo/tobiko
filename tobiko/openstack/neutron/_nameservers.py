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

import typing

from oslo_log import log
import netaddr

import tobiko
from tobiko.shell import ip
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


class DefaultNameserversFixture(sh.ListNameserversFixture):

    remove_local_ips = True
    max_count = 3
    ip_version = None

    @property
    def ssh_client(self):
        host = tobiko.tobiko_config().neutron.nameservers_host
        if host is None:
            return ssh.ssh_proxy_client()
        else:
            return ssh.ssh_client(host)

    @property
    def filenames(self):
        return tuple(tobiko.tobiko_config().neutron.nameservers_filenames)

    def setup_fixture(self):
        super(DefaultNameserversFixture, self).setup_fixture()
        if self.remove_local_ips:
            local_ips = ip.list_ip_addresses(scope='host')
            if local_ips:
                # Filter out all local IPs
                self.nameservers = tobiko.select(
                    nameserver for nameserver in self.nameservers
                    if nameserver not in local_ips)
        if self.max_count:
            actual_count = len(self.nameservers)
            if actual_count > self.max_count:
                LOG.waring("Limit the number of nameservers from "
                           f"{actual_count} to {self.max_count}")
                self.nameservers = self.nameservers[:3]


DEFAULT_NAMESERVERS_FIXTURE = DefaultNameserversFixture


def default_nameservers(
        ip_version: typing.Optional[int] = None) -> \
        tobiko.Selection[netaddr.IPAddress]:
    nameservers = tobiko.setup_fixture(
        DEFAULT_NAMESERVERS_FIXTURE).nameservers
    if ip_version is not None:
        nameservers = nameservers.with_attributes(version=ip_version)
    return nameservers
