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

import time

import testtools

from oslo_log import log

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.openstack import topology
from tobiko.shell import ping
from tobiko.shell import sh

LOG = log.getLogger(__name__)


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

    def get_process_pids_for_resource(self, process_name, command_filter,
                                      agents, timeout=120, interval=2):
        '''Search for PIDs that match creteria on requested hosts'''

        start_time = time.time()
        pids_per_agent = {}
        LOG.debug(f'Search for {process_name} processes on {agents}')
        for agent in agents:
            LOG.debug(f'Search for {process_name} process on {agent["host"]}')
            agent_host = topology.get_openstack_node(hostname=agent['host'])
            ssh_client = agent_host.ssh_client
            time_left = start_time + timeout - time.time()
            while time_left > 0:
                pid = self.get_pid(ssh_client, command_filter, process_name)
                if pid:
                    pids_per_agent[agent['host']] = pid
                    LOG.debug(f'{process_name} process has {pid} PID on '
                              f'{agent["host"]} host')
                    break
                time_left = start_time + timeout - time.time()
                LOG.debug(f'Retrying, time left: {time_left}')
                time.sleep(interval)
            if not pid:
                self.fail(f'No {process_name} process found on host '
                          f'{agent["host"]} that matches {command_filter}')
        return pids_per_agent

    def get_pid(self, ssh_client, command_filter, process_name):
        processes = sh.list_processes(command=process_name,
                                      ssh_client=ssh_client)
        for process in processes:
            try:
                command = sh.execute(f'cat /proc/{process.pid}/cmdline',
                                     ssh_client=ssh_client)
                if command_filter in command.stdout:
                    return process.pid
                else:
                    LOG.debug(f'No {command_filter} has been found in details'
                              f' of the following command: {command.stdout}')
            except sh.ShellCommandFailed:
                LOG.debug(f'Process {process.pid} has been terminated right '
                          f'after the process list has been collected')
        return None

    def wait_processes_destroyed(
            self, command_filter, pids_per_agent, timeout=120, interval=2):
        '''Wait for processes to be terminated on hosts

        Make sure that all processes from the list are terminated or return
        an error otherwise. Tricky situation may happen when the different
        process with same PID can be spawned so then need to check it against
        `command_filter`.
        '''

        start_time = time.time()
        LOG.debug(f'Waiting for processes to be finished: {pids_per_agent}')
        for agent, pid in pids_per_agent.items():
            host = topology.get_openstack_node(hostname=agent)
            destroyed = False
            time_left = start_time + timeout - time.time()
            while time_left > 0:
                LOG.debug(f'Check if {pid} has been terminated on {agent}')
                if self.is_destroyed(pid, command_filter, host.ssh_client):
                    destroyed = True
                    break
                time.sleep(interval)
                time_left = start_time + timeout - time.time()
                LOG.debug(f'Retrying, time left: {time_left}')
            if not destroyed:
                self.fail(f'Process {pid} has not been finished in {timeout}'
                          f' sec on {agent}')
            else:
                LOG.debug(f'Process {pid} has been finished on {agent}')

    def is_destroyed(self, pid, command_filter, shell):
        '''Check if process has been terminated'''

        processes = sh.list_processes(ssh_client=shell)
        process = processes.with_attributes(pid=pid)
        process_destroyed = False
        if not process:
            LOG.debug(f'No PID {pid} has been found in process list')
            process_destroyed = True
        else:
            try:
                command = sh.execute(f'cat /proc/{pid}/cmdline',
                                     ssh_client=shell)
                if command_filter not in command.stdout:
                    LOG.debug(f'Different process with same PID {pid} exist')
                    process_destroyed = True
            except sh.ShellCommandFailed:
                LOG.debug(f'Process {pid} has been terminated right after the'
                          f' process list has been collected')
                process_destroyed = True
        return process_destroyed


class DHCPAgentTest(testtools.TestCase, AgentTestMixin):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

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
        '''Test that dnsmasq processes are not broken after DHCP agent restart

        Dnsmasq processes should stay alive if DHCP agent is turned off and
        then restarted once DHCP agent is returned to active state.
        '''
        network_dhcp_agents = neutron.list_dhcp_agent_hosting_network(
            self.stack.network)
        network_dnsmasq_pids = self.get_process_pids_for_resource(
            "dnsmasq", self.stack.network, network_dhcp_agents)

        self.stop_service_on_agents(
            self.agent_service_name, network_dhcp_agents)
        self.assertEqual(
            network_dnsmasq_pids,
            self.get_process_pids_for_resource(
                "dnsmasq", self.stack.network, network_dhcp_agents))

        self.start_service_on_agents(
            self.agent_service_name, network_dhcp_agents)
        self.wait_processes_destroyed(self.stack.network, network_dnsmasq_pids)
        self.get_process_pids_for_resource(
            "dnsmasq", self.stack.network, network_dhcp_agents)

    def test_dhcp_lease_served_when_dhcp_agent_down(self):
        '''Test that DHCP lease is correctly served when DHCP agent is down

        Make sure that the VM will receive IP address after the reboot.
        DHCP agent should be down during the VM reboot. VM should receive
        the same IP address that was assigned to it before the reboot.
        '''
        ping.ping_until_received(
            self.stack.ip_address).assert_replied()

        network_dhcp_agents = neutron.list_dhcp_agent_hosting_network(
            self.stack.network)
        network_dnsmasq_pids = self.get_process_pids_for_resource(
            "dnsmasq", self.stack.network, network_dhcp_agents)
        self.stop_service_on_agents(
            self.agent_service_name, network_dhcp_agents)

        nova.shutoff_server(self.stack.resources.server.physical_resource_id)
        nova.activate_server(self.stack.resources.server.physical_resource_id)
        ping.ping_until_received(
            self.stack.ip_address).assert_replied()

        self.start_service_on_agents(
            self.agent_service_name, network_dhcp_agents)
        self.wait_processes_destroyed(self.stack.network, network_dnsmasq_pids)
        self.get_process_pids_for_resource(
            "dnsmasq", self.stack.network, network_dhcp_agents)


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


class OvsAgentTest(testtools.TestCase, AgentTestMixin):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    agent_type = 'Open vSwitch agent'

    def setUp(self):
        super(OvsAgentTest, self).setUp()
        os_topology = topology.get_openstack_topology()
        self.agent_service_name = os_topology.get_agent_service_name(
            "neutron-ovs-agent")
        if not self.agent_service_name:
            self.skip("Neutron OVS agent's service name not defined for "
                      "the topology %s" % os_topology)

        self.ovs_agents = neutron.list_agents(agent_type=self.agent_type)
        if not self.ovs_agents:
            self.skip("No Neutron OVS agents found in the cloud.")

        self.stopped_agents = []

    def tearDown(self):
        super(OvsAgentTest, self).tearDown()
        # Try to start all agents which may be down during the tests
        self.start_service_on_agents(
            self.agent_service_name, self.stopped_agents)

    def _get_agent_from_host(self, host):
        for agent in self.ovs_agents:
            if agent['host'] == host.name:
                return agent

    def test_vm_reachability_during_stop_ovs_agent(self):
        # Check if vm is reachable before test
        ping.ping_until_received(
            self.stack.ip_address).assert_replied()

        vm_host = topology.get_openstack_node(
            hostname=self.stack.hypervisor_host)
        agent = self._get_agent_from_host(vm_host)
        self.stop_service_on_agents(self.agent_service_name, [agent])
        ping.ping_until_received(
            self.stack.floating_ip_address).assert_replied()
        self.start_service_on_agents(self.agent_service_name, [agent])
