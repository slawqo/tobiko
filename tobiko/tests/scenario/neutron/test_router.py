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

import testtools

import tobiko
from tobiko import config
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.openstack import neutron
from tobiko.openstack import stacks
from tobiko.openstack import topology
from tobiko.tripleo import topology as tripleo_topology


CONF = config.CONF


class LegacyRouterTest(testtools.TestCase):
    """Test Neutron routers"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def setUp(self):
        super(LegacyRouterTest, self).setUp()
        if not self.stack.network_stack.has_gateway:
            tobiko.skip('Stack {!s} has no gateway',
                        self.stack.network_stack.stack_name)

        network_stack = self.stack.network_stack
        self.router = network_stack.gateway_details
        self.router_ipv4_address = network_stack.ipv4_subnet_gateway_ip
        self.router_ipv6_address = network_stack.ipv6_subnet_gateway_ip
        self.router_gateway_ip = network_stack.external_gateway_ips.first

        tripleo_topology.setup_tripleo_topology()
        self.topology = topology.get_openstack_topology()

    def test_internal_router_ipv4_interface_is_reachable(self):
        if not self.stack.network_stack.has_ipv4:
            tobiko.skip('Stack {!s} has no ipv4 subnet',
                        self.stack.network_stack.stack_name)
        ping.ping(
            self.router_ipv4_address,
            ssh_client=self.stack.ssh_client
        ).assert_replied()

    def test_internal_router_ipv6_interface_is_reachable(self):
        if not self.stack.network_stack.has_ipv6:
            tobiko.skip('Stack {!s} has no ipv6 subnet',
                        self.stack.network_stack.stack_name)
        ping.ping(
            self.router_ipv6_address,
            ssh_client=self.stack.ssh_client
        ).assert_replied()

    def test_router_gateway_is_reachable(self):
        ping.ping(
            self.router_gateway_ip,
            ssh_client=self.stack.ssh_client
        ).assert_replied()

    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_router_is_scheduled_on_l3_agents(self):
        self._test_router_is_scheduled_on_l3_agents()

    def test_router_ipv4_address(self):
        self.assertEqual(4, self.router_ipv4_address.version)
        ips = neutron.list_port_ip_addresses(
             port=self.stack.network_stack.ipv4_gateway_port_details,
             ip_version=4)
        self.assertIn(self.router_ipv4_address, ips)

    def test_router_ipv6_address(self):
        self.assertEqual(6, self.router_ipv6_address.version)
        ips = neutron.list_port_ip_addresses(
             port=self.stack.network_stack.ipv6_gateway_port_details,
             ip_version=6)
        self.assertIn(self.router_ipv6_address, ips)

        neutron.find_port_ip_address(
             port=self.stack.network_stack.ipv6_gateway_port_details,
             ip_version=6)

    def _get_l3_agent_nodes(self, hostname):
        hostname = hostname.split(".")
        for host in self.topology.nodes:
            if host.name in hostname:
                return host
        self.fail("Node with hostname %s not found in cloud topology" %
                  hostname)

    def _check_routers_namespace_on_host(self, hostname, state="master"):
        router_namespace = "qrouter-%s" % self.router['id']
        agent_host = self._get_l3_agent_nodes(hostname)
        ns_list = sh.execute(
            "sudo ip netns list", ssh_client=agent_host.ssh_client)
        self.assertIn(router_namespace, ns_list.stdout)
        ns_net_config = sh.execute(
            "sudo ip netns exec %s ip -o addr" % router_namespace,
            ssh_client=agent_host.ssh_client)
        if state == "master":
            self.assertIn(
                str(self.router_ipv4_address), ns_net_config.stdout)
            self.assertIn(
                str(self.router_ipv6_address), ns_net_config.stdout)
            self.assertIn(
                str(self.router_gateway_ip), ns_net_config.stdout)
        else:
            self.assertNotIn(
                str(self.router_ipv4_address), ns_net_config.stdout)
            self.assertNotIn(
                str(self.router_ipv6_address), ns_net_config.stdout)
            self.assertNotIn(
                str(self.router_gateway_ip), ns_net_config.stdout)

    def _test_router_is_scheduled_on_l3_agents(self):
        router_agent = neutron.find_l3_agent_hosting_router(self.router['id'],
                                                            unique=True)
        self._check_routers_namespace_on_host(router_agent['host'])


@neutron.skip_if_missing_networking_extensions('l3-ha')
class HaRouterTest(LegacyRouterTest):
    """Test Neutron HA routers"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.L3haServerStackFixture)

    def setUp(self):
        l3_agents = neutron.list_agents(agent_type="L3 agent")
        if len(l3_agents) < 2:
            neutron_extensions = neutron.get_networking_extensions()
            if "l3_agent_scheduler" in neutron_extensions:
                tobiko.skip("Ha router tests requires at least 2 L3 agents in "
                            "the cloud.")
        super(HaRouterTest, self).setUp()

    def _test_router_is_scheduled_on_l3_agents(self):
        router_agents = neutron.list_l3_agent_hosting_routers(
            self.router['id'])
        master_agent = router_agents.with_items(ha_state='active').unique
        backup_agents = router_agents.with_items(ha_state='standby')
        self.assertGreaterEqual(len(backup_agents), 1)
        self._check_routers_namespace_on_host(master_agent['host'])
        for backup_agent in backup_agents:
            self._check_routers_namespace_on_host(
                backup_agent['host'], state="backup")
