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

import netaddr

import tobiko

from tobiko.openstack.neutron import _client


def new_ipv4_cidr():
    return tobiko.setup_fixture(IPv4CIDRGeneratorFixture).new_cidr()


def new_ipv6_cidr():
    return tobiko.setup_fixture(IPv6CIDRGeneratorFixture).new_cidr()


class CIDRGeneratorFixture(tobiko.SharedFixture):

    cidr = None
    prefixlen = None
    client = None
    config = None
    cidr_generator = None

    def __init__(self, cidr=None, prefixlen=None, client=None):
        super(CIDRGeneratorFixture, self).__init__()
        if cidr:
            self.cidr = cidr
        if prefixlen:
            self.prefixlen = prefixlen
        if client:
            self.client = client

    def setup_fixture(self):
        self.setup_config()
        self.setup_client()
        self.setup_cidr_generator()

    def setup_config(self):
        from tobiko import config
        CONF = config.CONF
        self.config = CONF.tobiko.neutron

    def setup_client(self):
        self.client = _client.neutron_client(self.client)

    def setup_cidr_generator(self):
        self.cidr_generator = self.cidr.subnet(self.prefixlen)

    def new_cidr(self):
        used_cidrs = set(_client.list_subnet_cidrs(client=self.client))
        for cidr in self.cidr_generator:
            if cidr not in used_cidrs:
                return cidr
        raise NoSuchCIDRLeft(cidr=self.cidr, prefixlen=self.prefixlen)


class IPv4CIDRGeneratorFixture(CIDRGeneratorFixture):

    @property
    def cidr(self):
        return netaddr.IPNetwork(self.config.ipv4_cidr)

    @property
    def prefixlen(self):
        return int(self.config.ipv4_prefixlen)


class IPv6CIDRGeneratorFixture(CIDRGeneratorFixture):

    @property
    def cidr(self):
        return netaddr.IPNetwork(self.config.ipv6_cidr)

    @property
    def prefixlen(self):
        return int(self.config.ipv6_prefixlen)


class NoSuchCIDRLeft(tobiko.TobikoException):
    message = ("No such subnet CIDR left "
               "(CIDR={cidr!s}, prefixlen={prefixlen!s})")
