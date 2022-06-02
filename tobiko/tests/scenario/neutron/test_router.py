# Copyright (c) 2019 Red Hat
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

import pytest
from oslo_log import log
import testtools

import tobiko
from tobiko import config
from tobiko.shell import ping
from tobiko.shell import ip
from tobiko.shell import ssh
from tobiko.openstack import neutron
from tobiko.openstack import stacks
from tobiko.openstack import topology


LOG = log.getLogger(__name__)
CONF = config.CONF


@pytest.mark.minimal
class RouterTest(testtools.TestCase):
    """Test Neutron routers"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_fixture(stacks.CirrosServerStackFixture)

    def setUp(self):
        super(RouterTest, self).setUp()
        if not self.stack.network_stack.has_gateway:
            tobiko.skip_test(
                f"Stack {self.stack.network_stack.stack_name} has no gateway")

    @property
    def router(self):
        return self.stack.network_stack.gateway_details

    @property
    def ipv4_subnet_gateway_ip(self):
        if not self.stack.network_stack.has_ipv4:
            tobiko.skip_test(f"Stack {self.stack.network_stack.stack_name} "
                             "has no ipv4 subnet")
        return self.stack.network_stack.ipv4_subnet_gateway_ip

    @property
    def ipv6_subnet_gateway_ip(self):
        if not self.stack.network_stack.has_ipv6:
            tobiko.skip_test(f"Stack {self.stack.network_stack.stack_name} "
                             "has no ipv6 subnet")
        return self.stack.network_stack.ipv6_subnet_gateway_ip

    @property
    def external_gateway_ips(self):
        return self.stack.network_stack.external_gateway_ips

    @property
    def router_ips(self):
        return tobiko.select([self.ipv4_subnet_gateway_ip,
                              self.ipv6_subnet_gateway_ip] +
                             self.external_gateway_ips)

    @tobiko.retry_test_case(interval=30.)
    def test_internal_router_ipv4_interface_is_reachable(self):
        ping.assert_reachable_hosts([self.ipv4_subnet_gateway_ip],
                                    ssh_client=self.stack.ssh_client)

    @tobiko.retry_test_case(interval=30.)
    def test_internal_router_ipv6_interface_is_reachable(self):
        ping.assert_reachable_hosts([self.ipv6_subnet_gateway_ip],
                                    ssh_client=self.stack.ssh_client)

    def test_ipv4_subnet_gateway_ip(self):
        self.assertEqual(4, self.ipv4_subnet_gateway_ip.version)
        self.assertIn(self.ipv4_subnet_gateway_ip,
                      self.stack.network_stack.ipv4_gateway_addresses)

    def test_ipv6_subnet_gateway_ip(self):
        self.assertEqual(6, self.ipv6_subnet_gateway_ip.version)
        self.assertIn(self.ipv6_subnet_gateway_ip,
                      self.stack.network_stack.ipv6_gateway_addresses)

    @pytest.mark.flaky(reruns=3, reruns_delay=60)
    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_router_is_scheduled_on_l3_agents(self):
        router_agent = neutron.find_l3_agent_hosting_router(self.router['id'],
                                                            unique=True)
        self._check_routers_namespace_on_host(router_agent['host'])

    def _check_routers_namespace_on_host(self, hostname, state="master"):
        namespace_ips = self._get_router_ips_from_namespaces(hostname)
        missing_ips = set(self.router_ips) - set(namespace_ips)
        if state == "master":
            self.assertFalse(missing_ips)
        else:
            self.assertTrue(missing_ips)

    def _get_router_ips_from_namespaces(self, hostname):
        agent_host = topology.get_openstack_node(hostname=hostname)
        router_namespaces = ["qrouter-%s" % self.router['id']]
        if self.router.get('distributed'):
            router_namespaces.append("snat-%s" % self.router['id'])
        host_namespaces = ip.list_network_namespaces(
            ssh_client=agent_host.ssh_client)
        ips = []
        for router_namespace in router_namespaces:
            self.assertIn(router_namespace, host_namespaces)
            ips += ip.list_ip_addresses(
                scope='global', network_namespace=router_namespace,
                ssh_client=agent_host.ssh_client)
        return ips


@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class L3HARouterTest(RouterTest):
    """Test Neutron HA routers"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_fixture(stacks.L3haServerStackFixture)

    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_router_is_scheduled_on_l3_agents(self):
        master_agent, backup_agents = (
            neutron.wait_for_master_and_backup_agents(self.router['id']))
        self.assertGreaterEqual(len(backup_agents), 1)
        self._check_routers_namespace_on_host(master_agent['host'])
        for backup_agent in backup_agents:
            self._check_routers_namespace_on_host(
                backup_agent['host'], state="backup")


class DistributedRouterStackFixture(stacks.RouterStackFixture):
    distributed = True


@pytest.mark.ovn_migration
class RouterNamespaceTest(testtools.TestCase):

    server_stack = tobiko.required_fixture(stacks.CirrosServerStackFixture)
    distributed_router_stack = (
        tobiko.required_fixture(DistributedRouterStackFixture))

    @neutron.skip_unless_is_ovn()
    def test_router_namespace_on_ovn(self):
        """Check router namespace is being created on compute host

        When A VM running in a compute node is expected to route
        packages to a router, a network namespace is expected to exist on
        compute name that is named after the router ID
        """
        router = self.server_stack.network_stack.gateway_details
        self.assert_has_not_router_namespace(router=router)

    @neutron.skip_unless_is_ovs()
    def test_router_namespace_on_ovs(self):
        """Check router namespace is being created on compute host

        When A VM running in a compute node is expected to route
        packages to a router, a network namespace is expected to exist on
        compute name that is named after the router ID
        """
        router = self.server_stack.network_stack.gateway_details
        self.assert_has_router_namespace(router=router)

    @neutron.skip_unless_is_ovs()
    @neutron.skip_if_missing_networking_extensions('dvr')
    def test_distributed_router_namespace(self):
        """Test that no router namespace is created for DVR on compute node

        When A VM running in a compute node is not expected to route
        packages to a given router, a network namespace is not expected to
        exist on compute name that is named after the router ID
        """
        router = self.distributed_router_stack.router_details
        self.assertTrue(router['distributed'])
        self.assert_has_not_router_namespace(router=router)

    def assert_has_router_namespace(self, router: neutron.RouterType):
        router_namespace = f"qrouter-{router['id']}"
        self.assertIn(router_namespace,
                      self.list_network_namespaces(),
                      "No such router network namespace on hypervisor host")

    def assert_has_not_router_namespace(self, router: neutron.RouterType):
        router_namespace = f"qrouter-{router['id']}"
        self.assertNotIn(router_namespace,
                         self.list_network_namespaces(),
                         "Router network namespace found on hypervisor host")

    @property
    def hypervisor_ssh_client(self) -> ssh.SSHClientFixture:
        # Check the VM can reach a working gateway
        ping.assert_reachable_hosts([self.server_stack.ip_address])
        # List namespaces on hypervisor node
        hypervisor = topology.get_openstack_node(
            hostname=self.server_stack.hypervisor_host)
        return hypervisor.ssh_client

    def list_network_namespaces(self) -> typing.List[str]:
        return ip.list_network_namespaces(
            ssh_client=self.hypervisor_ssh_client)
