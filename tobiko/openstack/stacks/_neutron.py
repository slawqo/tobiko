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

import json
import typing

import netaddr
from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack import heat
from tobiko.openstack import neutron
from tobiko.openstack.stacks import _hot
from tobiko.shell import ip
from tobiko.shell import sh
from tobiko.shell import ssh


CONF = config.CONF
LOG = log.getLogger(__name__)

NeutronNetworkType = typing.Dict[str, typing.Any]


class ExternalNetworkStackFixture(heat.HeatStackFixture):

    template = _hot.heat_template_file('neutron/external_network.yaml')

    @property
    def external_name(self):
        return tobiko.tobiko_config().neutron.external_network

    subnet_enable_dhcp: typing.Optional[bool] = False

    _external_network: typing.Optional[NeutronNetworkType] = None

    @property
    def external_network(self) -> typing.Optional[NeutronNetworkType]:
        external_network = self._external_network
        if external_network is None:
            subnet_parameters = {}
            if self.subnet_enable_dhcp is not None:
                subnet_parameters['enable_dhcp'] = self.subnet_enable_dhcp
            for network in list_external_networks(name=self.external_name):
                if not network['subnets']:
                    LOG.debug(f"Network '{network['id']}' has any subnet")
                    continue
                subnets = neutron.list_subnets(network_id=network['id'],
                                               **subnet_parameters)
                if not subnets:
                    LOG.debug(f"Network '{network['id']}' has any valid "
                              f"subnet: {subnet_parameters}")
                    continue

                network_dump = json.dumps(network, indent=4, sort_keys=True)
                LOG.debug(f"Found external network for {self.fixture_name}:\n"
                          f"{network_dump}")

                subnets_dump = json.dumps(subnets, indent=4, sort_keys=True)
                LOG.debug(f"External subnets for {self.fixture_name}:\n"
                          f"{subnets_dump}")
                self._external_network = external_network = network
                break
            else:
                LOG.warning("No external network found for "
                            f"'{self.fixture_name}':\n"
                            f" - name or ID: {self.external_name}\n"
                            f" - subnet attributes: {subnet_parameters}\n")
        return external_network

    @property
    def external_id(self):
        network = self.external_network
        return network and network['id'] or None

    @property
    def has_external_id(self):
        return bool(self.external_id)

    @property
    def network_details(self):
        return neutron.get_network(self.network_id)

    has_gateway = False


class FloatingNetworkStackFixture(ExternalNetworkStackFixture):

    @property
    def external_name(self):
        return tobiko.tobiko_config().neutron.floating_network

    subnet_enable_dhcp = None


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
        return bool(CONF.tobiko.neutron.ipv6_cidr)

    @property
    def ipv6_cidr(self):
        if self.has_ipv6:
            return neutron.new_ipv6_cidr(seed=self.fixture_name)
        else:
            return None

    @property
    def network_value_specs(self):
        """Extra network creation parameters"""
        return {}

    floating_network_stack = tobiko.required_setup_fixture(
        FloatingNetworkStackFixture)

    @property
    def floating_network(self):
        """Network ID where the Neutron floating IPs are created"""
        return self.floating_network_stack.network_id

    @property
    def gateway_network(self):
        """Network ID where gateway routes packages to"""
        return self.floating_network

    ha = False

    @property
    def gateway_value_specs(self):
        value_specs = {}
        if self.has_l3_ha:
            value_specs.update(ha=(self.ha or False))
        return value_specs

    @property
    def has_gateway(self):
        """Whenever to setup gateway router"""
        return bool(self.gateway_network)

    @property
    def has_net_mtu(self):
        """Whenever can obtain network MTU value"""
        return neutron.has_networking_extensions('net-mtu')

    @property
    def has_l3_ha(self):
        """Whenever can obtain gateway router HA value"""
        return neutron.has_networking_extensions('l3-ha')

    @property
    def network_details(self):
        return neutron.get_network(self.network_id)

    @property
    def ipv4_subnet_details(self):
        return neutron.get_subnet(self.ipv4_subnet_id)

    @property
    def ipv4_subnet_cidr(self):
        return netaddr.IPNetwork(self.ipv4_subnet_details['cidr'])

    @property
    def ipv4_subnet_gateway_ip(self):
        return netaddr.IPAddress(self.ipv4_subnet_details['gateway_ip'])

    @property
    def ipv4_dns_nameservers(self):
        nameservers = CONF.tobiko.neutron.ipv4_dns_nameservers
        if nameservers is None:
            nameservers = default_nameservers(ip_version=4)
        return ','.join(str(nameserver) for nameserver in nameservers)

    @property
    def ipv6_subnet_details(self):
        return neutron.get_subnet(self.ipv6_subnet_id)

    @property
    def ipv6_subnet_cidr(self):
        return netaddr.IPNetwork(self.ipv6_subnet_details['cidr'])

    @property
    def ipv6_subnet_gateway_ip(self):
        return netaddr.IPAddress(self.ipv6_subnet_details['gateway_ip'])

    @property
    def ipv6_dns_nameservers(self):
        nameservers = CONF.tobiko.neutron.ipv6_dns_nameservers
        if nameservers is None:
            nameservers = default_nameservers(ip_version=6)
        return ','.join(str(nameserver) for nameserver in nameservers)

    @property
    def gateway_details(self):
        return neutron.get_router(self.gateway_id)

    @property
    def external_gateway_ips(self):
        fixed_ips = self.gateway_details['external_gateway_info'][
            'external_fixed_ips']
        return tobiko.select(netaddr.IPAddress(fixed_ip['ip_address'])
                             for fixed_ip in fixed_ips)

    @property
    def ipv4_gateway_ports(self):
        return neutron.list_ports(fixed_ips='subnet_id=' + self.ipv4_subnet_id,
                                  device_id=self.gateway_id,
                                  network_id=self.network_id)

    @property
    def ipv6_gateway_ports(self):
        return neutron.list_ports(fixed_ips='subnet_id=' + self.ipv6_subnet_id,
                                  device_id=self.gateway_id,
                                  network_id=self.network_id)

    @property
    def external_geteway_ports(self):
        return neutron.list_ports(device_id=self.gateway_id,
                                  network_id=self.gateway_network_id)

    @property
    def ipv4_gateway_addresses(self):
        ips = tobiko.Selection()
        for port in self.ipv4_gateway_ports:
            ips.extend(neutron.list_port_ip_addresses(port))
        return ips

    @property
    def ipv6_gateway_addresses(self):
        ips = tobiko.Selection()
        for port in self.ipv6_gateway_ports:
            ips.extend(neutron.list_port_ip_addresses(port))
        return ips

    @property
    def external_gateway_addresses(self):
        ips = tobiko.Selection()
        for port in self.external_geteway_ports:
            ips.extend(neutron.list_port_ip_addresses(port))
        return ips

    @property
    def gateway_network_details(self):
        return neutron.get_network(self.gateway_network_id)

    @property
    def neutron_required_quota_set(self) -> typing.Dict[str, int]:
        requirements = super().neutron_required_quota_set
        requirements['network'] += 1
        if self.has_ipv4:
            requirements['subnet'] += 1
        if self.has_ipv6:
            requirements['subnet'] += 1
        if self.has_gateway:
            requirements['router'] += 1
        return requirements


@neutron.skip_if_missing_networking_extensions('net-mtu-writable')
class NetworkWithNetMtuWriteStackFixture(NetworkStackFixture):

    @property
    def custom_mtu_size(self):
        return CONF.tobiko.neutron.custom_mtu_size

    @property
    def network_value_specs(self):
        value_specs = super(NetworkWithNetMtuWriteStackFixture,
                            self).network_value_specs
        return dict(value_specs, mtu=self.custom_mtu_size)


@neutron.skip_if_missing_networking_extensions('security-group')
class SecurityGroupsFixture(heat.HeatStackFixture):
    """Heat stack with some security groups

    """
    #: Heat template file
    template = _hot.heat_template_file('neutron/security_groups.yaml')


def list_external_networks(name: typing.Optional[str] = None) -> \
        tobiko.Selection[NeutronNetworkType]:
    networks = tobiko.Selection[NeutronNetworkType]()
    if name is not None:
        try:
            network = neutron.get_network(name)
        except neutron.NoSuchNetwork:
            LOG.error(f"No such network with ID '{name}'")
        else:
            networks.append(network)
    if not networks:
        network_params = {'router:external': True, "status": "ACTIVE"}
        if name is not None:
            network_params['name'] = name
        networks += neutron.list_networks(**network_params)
    if not networks and name:
        raise ValueError("No such external network with name or ID "
                         f"'{name}'")
    return networks


def get_external_network_id():
    return tobiko.setup_fixture(ExternalNetworkStackFixture).network_id


def get_external_network():
    return tobiko.setup_fixture(ExternalNetworkStackFixture).network_details


def has_external_network():
    return tobiko.setup_fixture(ExternalNetworkStackFixture).has_network


skip_unless_has_external_network = tobiko.skip_unless(
    'External network not found', has_external_network)


def get_floating_network_id():
    return tobiko.setup_fixture(FloatingNetworkStackFixture).network_id


def get_floating_network():
    return tobiko.setup_fixture(FloatingNetworkStackFixture).network_details


def has_floating_network():
    return tobiko.setup_fixture(FloatingNetworkStackFixture).has_network


skip_unless_has_floating_network = tobiko.skip_unless(
    'Floating network not found', has_floating_network)


class DefaultNameserversFixture(tobiko.SharedFixture):

    remove_local_ips = True
    max_count = 3
    ip_version = None

    nameservers: typing.Optional[tobiko.Selection[netaddr.IPAddress]] = None

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
        self.nameservers = self.list_nameservers()

    def list_nameservers(self) -> tobiko.Selection[netaddr.IPAddress]:
        nameservers: tobiko.Selection[netaddr.IPAddress]
        if has_external_network():
            network_id = get_external_network_id()
            nameservers = neutron.list_network_nameservers(
                network_id=network_id)
            LOG.debug("Nameservers copied from external network: "
                      f"{nameservers}")
        else:
            # Copy nameservers from target host
            nameservers = sh.list_nameservers(ssh_client=self.ssh_client,
                                              ip_version=self.ip_version,
                                              filenames=self.filenames)
            if self.remove_local_ips:
                local_ips = ip.list_ip_addresses(scope='host')
                if local_ips:
                    # Filter out all local IPs
                    nameservers = tobiko.Selection[netaddr.IPAddress](
                        nameserver for nameserver in nameservers
                        if nameserver not in local_ips)
            LOG.debug(f"Nameservers copied from host: {nameservers}")
        if self.max_count:
            # Keep only up to max_count nameservers
            actual_count = len(nameservers)
            if actual_count > self.max_count:
                LOG.waring("Limit the number of nameservers from "
                           f"{actual_count} to {self.max_count}: "
                           f"{nameservers}")
                nameservers = tobiko.Selection[netaddr.IPAddress](
                    nameservers[:self.max_count])
        return nameservers


DEFAULT_NAMESERVERS_FIXTURE = DefaultNameserversFixture


def default_nameservers(
        ip_version: typing.Optional[int] = None) -> \
        tobiko.Selection[netaddr.IPAddress]:
    nameservers = tobiko.setup_fixture(
        DEFAULT_NAMESERVERS_FIXTURE).nameservers
    if ip_version is not None:
        nameservers = nameservers.with_attributes(version=ip_version)
    return nameservers
