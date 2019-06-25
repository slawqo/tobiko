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

import netaddr
from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack import heat
from tobiko.openstack import neutron
from tobiko.openstack import images
from tobiko.openstack.stacks import _hot
from tobiko.openstack.stacks import _nova
from tobiko.shell import ssh


CONF = config.CONF
LOG = log.getLogger(__name__)


@neutron.skip_if_missing_networking_extensions('port-security')
class NetworkStackFixture(heat.HeatStackFixture):
    """Heat stack for creating internal network with a router to external"""

    #: Heat template file
    template = _hot.heat_template_file('neutron/network.yaml')

    #: Disable port security by default for new network ports
    port_security_enabled = False

    @property
    def has_ipv4(self):
        """Whenever to setup IPv4 subnet"""
        return bool(CONF.tobiko.neutron.ipv4_cidr)

    @property
    def ipv4_cidr(self):
        if self.has_ipv4:
            return neutron.new_ipv4_cidr(seed=self.fixture_name)
        else:
            return None

    @property
    def has_ipv6(self):
        """Whenever to setup IPv6 subnet"""
        return bool(CONF.tobiko.neutron.ipv4_cidr)

    @property
    def ipv6_cidr(self):
        if self.has_ipv6:
            return neutron.new_ipv6_cidr(seed=self.fixture_name)
        else:
            return None

    @property
    def value_specs(self):
        return {}

    @property
    def gateway_network(self):
        """Floating IP network where the Neutron floating IPs are created"""
        return CONF.tobiko.neutron.floating_network

    @property
    def has_gateway(self):
        """Whenever to setup gateway router"""
        return bool(self.gateway_network)

    @property
    def has_net_mtu(self):
        """Whenever can obtain network MTU value"""
        return neutron.has_networking_extensions('net-mtu')

    @property
    def network_details(self):
        return neutron.show_network(self.network_id)

    @property
    def ipv4_subnet_details(self):
        return neutron.show_subnet(self.ipv4_subnet_id)

    @property
    def ipv4_subnet_cidr(self):
        return netaddr.IPNetwork(self.ipv4_subnet_details['cidr'])

    @property
    def ipv6_subnet_details(self):
        return neutron.show_subnet(self.ipv6_subnet_id)

    @property
    def ipv6_subnet_cidr(self):
        return netaddr.IPNetwork(self.ipv6_subnet_details['cidr'])

    @property
    def gateway_details(self):
        return neutron.show_router(self.gateway_id)

    @property
    def ipv4_gateway_port_details(self):
        return neutron.find_port(
            [{'subnet_id': self.ipv4_subnet_id,
              'ip_address': self.ipv4_subnet_details['gateway_ip']}],
            properties=['fixed_ips'],
            device_id=self.gateway_id,
            network_id=self.network_id)

    @property
    def ipv6_gateway_port_details(self):
        return neutron.find_port(
            [{'subnet_id': self.ipv6_subnet_id,
              'ip_address': self.ipv6_subnet_details['gateway_ip']}],
            properties=['fixed_ips'],
            device_id=self.gateway_id,
            network_id=self.network_id)

    @property
    def gateway_network_details(self):
        return neutron.show_network(self.gateway_network_id)


@neutron.skip_if_missing_networking_extensions('net-mtu-writable')
class NetworkWithNetMtuWriteStackFixture(NetworkStackFixture):

    @property
    def custom_mtu_size(self):
        return CONF.tobiko.neutron.custom_mtu_size

    @property
    def value_specs(self):
        value_specs = super(
            NetworkWithNetMtuWriteStackFixture, self).value_specs
        return dict(value_specs, mtu=self.custom_mtu_size)


@neutron.skip_if_missing_networking_extensions('security-group')
class SecurityGroupsFixture(heat.HeatStackFixture):
    """Heat stack with some security groups

    """
    #: Heat template file
    template = _hot.heat_template_file('neutron/security_groups.yaml')


@neutron.skip_if_missing_networking_extensions('port-security')
class FloatingIpServerStackFixture(heat.HeatStackFixture):

    #: Heat template file
    template = _hot.heat_template_file('neutron/floating_ip_server.yaml')

    #: stack with the key pair for the server instance
    key_pair_stack = tobiko.required_setup_fixture(
        _nova.KeyPairStackFixture)

    #: stack with the internal where the server port is created
    network_stack = tobiko.required_setup_fixture(NetworkStackFixture)

    #: Glance image used to create a Nova server instance
    image_fixture = tobiko.required_setup_fixture(images.CirrosImageFixture)

    @property
    def image(self):
        return self.image_fixture.image_id

    @property
    def username(self):
        """username used to login to a Nova server instance"""
        return self.image_fixture.username

    @property
    def password(self):
        """password used to login to a Nova server instance"""
        return self.image_fixture.password

    #: Nova flavor used to create a Nova server instance
    flavor = CONF.tobiko.nova.flavor

    #: Whenever port security on internal network is enable
    port_security_enabled = False

    #: Security groups to be associated to network ports
    security_groups = []

    @property
    def key_name(self):
        return self.key_pair_stack.key_name

    @property
    def network(self):
        return self.network_stack.network_id

    #: Floating IP network where the Neutron floating IP is created
    floating_network = CONF.tobiko.neutron.floating_network

    @property
    def has_floating_ip(self):
        return bool(self.floating_network)

    @property
    def ssh_client(self):
        return ssh.ssh_client(
            host=self.floating_ip_address,
            username=self.username,
            password=self.password)

    @property
    def ssh_command(self):
        return ssh.ssh_command(
            host=self.floating_ip_address,
            username=self.username)
