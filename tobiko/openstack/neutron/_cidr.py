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

import os
import random

import netaddr
from netaddr.strategy import ipv4
from netaddr.strategy import ipv6

import tobiko
from tobiko.openstack.neutron import _client


def new_ipv4_cidr(seed=None):
    return tobiko.setup_fixture(IPv4CIDRGeneratorFixture).new_cidr(seed=seed)


def new_ipv6_cidr(seed=None):
    return tobiko.setup_fixture(IPv6CIDRGeneratorFixture).new_cidr(seed=seed)


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

    def setup_config(self):
        from tobiko import config
        CONF = config.CONF
        self.config = CONF.tobiko.neutron

    def setup_client(self):
        self.client = _client.neutron_client(self.client)

    def new_cidr(self, seed):
        used_cidrs = set(_client.list_subnet_cidrs(client=self.client))
        for cidr in random_subnets(cidr=self.cidr, prefixlen=self.prefixlen,
                                   seed=seed):
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


def random_subnets(cidr, prefixlen, seed=None):
    """
    A generator that divides up this IPNetwork's subnet into smaller
    subnets based on a specified CIDR prefix.

    :param prefixlen: a CIDR prefix indicating size of subnets to be
        returned.

    :return: an iterator containing random IPNetwork subnet objects.
    """

    version = cidr.version
    module = {4: ipv4, 6: ipv6}[version]
    width = module.width
    if not 0 <= cidr.prefixlen <= width:
        message = "CIDR prefix /{!r} invalid for IPv{!s}!".format(
            prefixlen, cidr.version)
        raise ValueError(message)

    if not cidr.prefixlen <= prefixlen:
        #   Don't return anything.
        raise StopIteration

    # Calculate number of subnets to be returned.
    max_subnets = 2 ** (width - cidr.prefixlen) // 2 ** (width - prefixlen)

    base_subnet = module.int_to_str(cidr.first)
    i = 0
    rand = random.Random(hash(seed) ^ os.getpid())
    while True:
        subnet = netaddr.IPNetwork('%s/%d' % (base_subnet, prefixlen), version)
        subnet.value += (subnet.size * rand.randrange(0, max_subnets))
        subnet.prefixlen = prefixlen
        i += 1
        yield subnet
