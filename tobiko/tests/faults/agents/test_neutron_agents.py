# Copyright (c) 2020 Red Hat
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
from tobiko.openstack import neutron
from tobiko.openstack import stacks
from tobiko.openstack import topology
from tobiko.shell import sh


class AgentTestMixin(object):

    def stop_service_on_agents(self, service_name, agents):
        for agent in agents:
            agent_host = topology.get_openstack_node(hostname=agent['host'])
            sh.execute(
                "sudo systemctl stop %s" % service_name,
                ssh_client=agent_host.ssh_client)
            self.stopped_agents.append(agent)

    def start_service_on_agents(self, service_name, agents):
        for agent in agents:
            agent_host = topology.get_openstack_node(hostname=agent['host'])
            sh.execute(
                "sudo systemctl start %s" % service_name,
                ssh_client=agent_host.ssh_client)

    def get_process_pids_for_resource(self, process_name, resource_id, agents):
        pids_per_agent = {}
        for agent in agents:
            agent_host = topology.get_openstack_node(hostname=agent['host'])
            processes_on_host = sh.list_processes(
                command=process_name, ssh_client=agent_host.ssh_client)
            pid = self.get_pid(
                agent_host.ssh_client, resource_id, processes_on_host)
            if not pid:
                self.fail("%(process)s process for router: %(id)s "
                          "not found on host %(host)s" % {
                              'process': process_name,
                              'id': resource_id,
                              'host': agent['host']})
            pids_per_agent[agent['host']] = pid
        return pids_per_agent

    def get_pid(self, ssh_client, resource_id, processes):
        for process in processes:
            cmdline_result = sh.execute(
                "cat /proc/%s/cmdline" % process.pid, ssh_client=ssh_client)
            if resource_id in cmdline_result.stdout:
                return process.pid
        return None


class DHCPAgentTest(testtools.TestCase, AgentTestMixin):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosPeerServerStackFixture)

    def setUp(self):
        super(DHCPAgentTest, self).setUp()
        os_topology = topology.get_openstack_topology()
        self.agent_service_name = os_topology.get_agent_service_name(
            "neutron-dhcp-agent")
        if not self.agent_service_name:
            self.skip("Neutron DHCP agent's service name not defined for "
                      "the topology %s" % os_topology)
        self.stopped_agents = []

    def tearDown(self):
        super(DHCPAgentTest, self).tearDown()
        # Try to start all agents which may be down during the tests
        self.start_service_on_agents(
            self.agent_service_name, self.stopped_agents)

    def test_stop_dhcp_agent(self):
        network_dhcp_agents = neutron.list_dhcp_agent_hosting_network(
            self.stack.network)
        network_dnsmasq_pids = self.get_process_pids_for_resource(
            "dnsmasq", self.stack.network, network_dhcp_agents)
        self.stop_service_on_agents(
            self.agent_service_name, network_dhcp_agents)
        # Now check if dnsmasq processes are still run and have got same pids
        # like before dhcp agent's stop
        self.assertEqual(
            network_dnsmasq_pids,
            self.get_process_pids_for_resource(
                "dnsmasq", self.stack.network, network_dhcp_agents))

        self.start_service_on_agents(
            self.agent_service_name, network_dhcp_agents)

        # And finally check if dnsmasq processes are still run and have got
        # same pids like at the beginning of the test
        self.assertEqual(
            network_dnsmasq_pids,
            self.get_process_pids_for_resource(
                "dnsmasq", self.stack.network, network_dhcp_agents))


class L3AgentTest(testtools.TestCase, AgentTestMixin):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosPeerServerStackFixture)

    def setUp(self):
        super(L3AgentTest, self).setUp()
        os_topology = topology.get_openstack_topology()
        self.agent_service_name = os_topology.get_agent_service_name(
            "neutron-l3-agent")
        if not self.agent_service_name:
            self.skip("Neutron L3 agent's service name not defined for "
                      "the topology %s" % os_topology)
        self.router_id = self.stack.network_stack.gateway_id
        self.stopped_agents = []

    def tearDown(self):
        super(L3AgentTest, self).tearDown()
        # Try to start all agents which may be down during the tests
        self.start_service_on_agents(
            self.agent_service_name, self.stopped_agents)

    def test_metadata_haproxy_during_stop_L3_agent(self):
        network_l3_agents = neutron.list_l3_agent_hosting_routers(
            self.router_id)
        router_haproxy_pids = self.get_process_pids_for_resource(
            "haproxy", self.router_id, network_l3_agents)
        self.stop_service_on_agents(self.agent_service_name, network_l3_agents)
        # Now check if haproxy processes are still run and have got same pids
        # like before dhcp agent's stop
        self.assertEqual(
            router_haproxy_pids,
            self.get_process_pids_for_resource(
                "haproxy", self.router_id, network_l3_agents))

        self.start_service_on_agents(
            self.agent_service_name, network_l3_agents)

        # And finally check if haproxy processes are still run and have got
        # same pids like at the beginning of the test
        self.assertEqual(
            router_haproxy_pids,
            self.get_process_pids_for_resource(
                "haproxy", self.router_id, network_l3_agents))

    def _is_radvd_process_expected(self):
        stateless_modes = ['slaac', 'dhcpv6-stateless']
        ipv6_ra_mode = self.stack.network_stack.ipv6_subnet_details.get(
            'ipv6_ra_mode')
        ipv6_address_mode = self.stack.network_stack.ipv6_subnet_details.get(
            'ipv6_address_mode')
        if not self.stack.network_stack.ipv6_cidr:
            return False
        if (ipv6_ra_mode not in stateless_modes or
                ipv6_address_mode not in stateless_modes):
            return False
        return True

    def test_radvd_during_stop_l3_agent(self):
        if not self._is_radvd_process_expected():
            self.skip("Radvd process is not expected to be run on router %s" %
                      self.router_id)

        network_l3_agents = neutron.list_l3_agent_hosting_routers(
            self.router_id)
        router_radvd_pids = self.get_process_pids_for_resource(
            "radvd", self.router_id, network_l3_agents)
        self.stop_service_on_agents(self.agent_service_name, network_l3_agents)
        # Now check if radvd processes are still run and have got same pids
        # like before dhcp agent's stop
        self.assertEqual(
            router_radvd_pids,
            self.get_process_pids_for_resource(
                "radvd", self.router_id, network_l3_agents))

        self.start_service_on_agents(
            self.agent_service_name, network_l3_agents)

        # And finally check if dnsmasq processes are still run and have got
        # same pids like at the beginning of the test
        self.assertEqual(
            router_radvd_pids,
            self.get_process_pids_for_resource(
                "radvd", self.router_id, network_l3_agents))
