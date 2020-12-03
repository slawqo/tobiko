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
from tobiko.shell import ip
from tobiko.openstack import neutron
from tobiko.openstack import stacks
from tobiko.openstack import topology


CONF = config.CONF


class RouterTest(testtools.TestCase):
    """Test Neutron routers"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

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

    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_router_is_scheduled_on_l3_agents(self):
        router_agent = neutron.find_l3_agent_hosting_router(self.router['id'],
                                                            unique=True)
        self._check_routers_namespace_on_host(router_agent['host'])

    def _check_routers_namespace_on_host(self, hostname, state="master"):
        router_namespace = "qrouter-%s" % self.router['id']
        agent_host = topology.get_openstack_node(hostname=hostname)
        namespaces = ip.list_network_namespaces(
            ssh_client=agent_host.ssh_client)
        self.assertIn(router_namespace, namespaces)
        namespace_ips = ip.list_ip_addresses(
            scope='global', network_namespace=router_namespace,
            ssh_client=agent_host.ssh_client)
        missing_ips = set(self.router_ips) - set(namespace_ips)
        if state == "master":
            self.assertFalse(missing_ips)
        else:
            self.assertTrue(missing_ips)


@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class L3HARouterTest(RouterTest):
    """Test Neutron HA routers"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.L3haServerStackFixture)

    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_router_is_scheduled_on_l3_agents(self):
        router_agents = neutron.list_l3_agent_hosting_routers(
            self.router['id'])
        master_agent = router_agents.with_items(ha_state='active').unique
        backup_agents = router_agents.with_items(ha_state='standby')
        self.assertGreaterEqual(len(backup_agents), 1)
        self._check_routers_namespace_on_host(master_agent['host'])
        for backup_agent in backup_agents:
            self._check_routers_namespace_on_host(
                backup_agent['host'], state="backup")
