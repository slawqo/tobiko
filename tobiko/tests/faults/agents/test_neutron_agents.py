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


class DHCPAgentTest(testtools.TestCase):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosPeerServerStackFixture)

    def setUp(self):
        super(DHCPAgentTest, self).setUp()
        os_topology = topology.get_openstack_topology()
        self.dhcp_agent_service_name = os_topology.get_agent_service_name(
            "neutron-dhcp-agent")
        if not self.dhcp_agent_service_name:
            self.skip("Neutron DHCP agent's service name not defined for "
                      "the topology %s" % os_topology)

    def test_stop_dhcp_agent(self):
        network_dhcp_agents = neutron.list_dhcp_agent_hosting_network(
            self.stack.network)
        network_dnsmasq_pids = self._get_dnsmasq_pids_for_network(
            self.stack.network, network_dhcp_agents)
        self._stop_dhcp_agent_on_hosts(network_dhcp_agents)
        # Now check if dnsmasq processes are still run and have got same pids
        # like before dhcp agent's stop
        self.assertEqual(
            network_dnsmasq_pids,
            self._get_dnsmasq_pids_for_network(self.stack.network,
                                               network_dhcp_agents))

        self._start_dhcp_agent_on_hosts(network_dhcp_agents)

        # And finally check if dnsmasq processes are still run and have got
        # same pids like at the beginning of the test
        self.assertEqual(
            network_dnsmasq_pids,
            self._get_dnsmasq_pids_for_network(self.stack.network,
                                               network_dhcp_agents))

    def _get_dnsmasq_pids_for_network(self, network_id, agents):
        dnsmasq_pids_per_agent = {}
        for agent in agents:
            agent_host = topology.get_openstack_node(hostname=agent['host'])
            dnsmasq_processes_on_host = sh.list_processes(
                command="dnsmasq", ssh_client=agent_host.ssh_client)
            dnsmasq_pid = self._get_dnsmasq_pid_for_network(
                agent_host.ssh_client, network_id,
                dnsmasq_processes_on_host)
            if not dnsmasq_pid:
                self.fail("Dnsmasq process for network: %(network_id)s "
                          "not found on host %(host)s" % {
                              'network_id': network_id,
                              'host': agent['host']})
            dnsmasq_pids_per_agent[agent['host']] = dnsmasq_pid
        return dnsmasq_pids_per_agent

    def _get_dnsmasq_pid_for_network(self, ssh_client, network_id, processes):
        for process in processes:
            cmdline_result = sh.execute(
                "cat /proc/%s/cmdline" % process.pid, ssh_client=ssh_client)
            if network_id in cmdline_result.stdout:
                return process.pid
        return None

    def _stop_dhcp_agent_on_hosts(self, agents):
        for agent in agents:
            agent_host = topology.get_openstack_node(hostname=agent['host'])
            sh.execute(
                "sudo systemctl stop %s" % self.dhcp_agent_service_name,
                ssh_client=agent_host.ssh_client)

    def _start_dhcp_agent_on_hosts(self, agents):
        for agent in agents:
            agent_host = topology.get_openstack_node(hostname=agent['host'])
            sh.execute(
                "sudo systemctl start %s" % self.dhcp_agent_service_name,
                ssh_client=agent_host.ssh_client)
