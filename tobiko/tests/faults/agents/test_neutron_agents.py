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

import re

from oslo_log import log
import testtools

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.openstack import topology
from tobiko.shell import ping
from tobiko.shell import sh


LOG = log.getLogger(__name__)


class AgentTestMixin(object):

    def stop_service_on_hosts(self, service_name, hosts):
        '''Stop systemd service on hosts

        :param service_name: Name of the systemd service
        :type service_name: string
        :parm hosts: List of hostnames to stop service on
        :type hosts: list of strings
        '''
        for host in hosts:
            agent_host = topology.get_openstack_node(hostname=host)
            LOG.debug(f'Trying to stop {service_name} on {host}')
            sh.execute(
                "sudo systemctl stop %s" % service_name,
                ssh_client=agent_host.ssh_client)
            self.stopped_agent_hosts.append(host)

    def start_service_on_hosts(self, service_name, hosts):
        '''Start systemd service on hosts

        :param service_name: Name of the systemd service
        :type service_name: string
        :parm hosts: List of hostnames to start service on
        :type hosts: list of strings
        '''
        for host in hosts:
            agent_host = topology.get_openstack_node(hostname=host)
            LOG.debug(f'Trying to start {service_name} on {host}')
            sh.execute(
                "sudo systemctl start %s" % service_name,
                ssh_client=agent_host.ssh_client)

    def get_cmd_pids(self, process_name, command_filter, hosts,
                     timeout=120, interval=2, min_pids_per_host=1):
        '''Search for PIDs that match creteria on requested hosts

        :param process_name: Name of the executable of the process
        :type process_name: string
        :parm command_filter: Regex to be found in process command details
        :type command_filter: string
        :param hosts: List of hostnames to search for processes on
        :type hosts: list of strings
        :param timeout: Time to search for processes
        :type timeout: int
        :param interval: Time to wait between searching attempts
        :param min_pids_per_host: Minimum amount of processes to be found
        :type min_pids_per_host: int
        :return: Dictionary with hostnames as a key and list of PIDs as value
        :rtype: dict
        '''
        pids_per_host = {}
        LOG.debug(f'Search for {process_name} processes on {hosts}')
        for host in hosts:
            LOG.debug(f'Search for {process_name} process on {host}')
            retry = tobiko.retry(timeout=timeout, interval=interval)
            for _ in retry:
                pids = self.list_pids(host, command_filter, process_name)
                if len(pids) >= min_pids_per_host:
                    pids_per_host[host] = pids
                    LOG.debug(f'{process_name} process has {pids} PIDs list on'
                              f' {host} host')
                    break
        return pids_per_host

    def list_pids(self, host, command_filter, process_name):
        '''Search for PIDs matched with filter and process name

        :param host: Hostname of the node to search processes on
        :type host: string
        :param command_filter: Regex to be found in process command details
        :type command_filter: string
        :param process_name: Name of the executable in process list
        :type process_name: string
        '''
        ssh_client = topology.get_openstack_node(hostname=host).ssh_client
        processes = sh.list_processes(command=process_name,
                                      ssh_client=ssh_client)
        pids = []
        for process in processes:
            try:
                command = sh.execute(f'cat /proc/{process.pid}/cmdline',
                                     ssh_client=ssh_client)
                if re.search(command_filter, command.stdout):
                    pids.append(process.pid)
            except sh.ShellCommandFailed:
                LOG.debug(f'Process {process.pid} has been terminated right '
                          f'after the process list has been collected')
        return pids

    def kill_pids(self, host, pids):
        '''Kill processes with specific PIDs on the host

        :param host: Hostname of the node to kill processes on
        :type host: string
        :param pids: List of PIDs to be killed
        :type pids: list of int
        '''
        ssh_client = topology.get_openstack_node(hostname=host).ssh_client
        pid_args = ' '.join(str(pid) for pid in pids)
        sh.execute(f'kill -15 {pid_args}', ssh_client=ssh_client, sudo=True)
        retry = tobiko.retry(timeout=60, interval=2)
        for _ in retry:
            pid_status = sh.execute(f'kill -0 {pid_args}',
                                    ssh_client=ssh_client,
                                    expect_exit_status=None,
                                    sudo=True).stderr.strip().split('\n')
            if all('No such process' in status for status in pid_status) and \
                    len(pid_status) == len(pids):
                break

    def wait_processes_destroyed(self, command_filter, pids_per_host,
                                 timeout=120, interval=2):
        '''Wait for processes to be terminated on hosts

        Make sure that all processes from the list are terminated or return
        an error otherwise. Tricky situation may happen when the different
        process with same PID can be spawned so then need to check it against
        `command_filter`.

        :param command_filter: Patter to be found in process command details
        :type command_filter: string
        :param pids_per_host: Dictionary with hostnames as a key and list of
                PIDs as a value
        :type pids_per_host: dict
        :param timeout: Time to wait till each process will be terminated
        :type timeout: int
        :param interval: Time to sleep between attempts
        :type interval: int
        '''
        LOG.debug(f'Waiting for processes to be finished: {pids_per_host}')
        for host, pids in pids_per_host.items():
            for pid in pids:
                retry = tobiko.retry(timeout=timeout, interval=interval)
                for _ in retry:
                    LOG.debug(f'Check if {pid} has been terminated on {host}')
                    if self.is_destroyed(pid, command_filter, host):
                        LOG.debug(f'Process {pid} finished on {host}')
                        break

    def is_destroyed(self, pid, command_filter, hostname):
        '''Check if process has been terminated

        :param pid: Process ID to check if exist and handles specific command
        :type pid: int
        :param command_filter: Patter to be found in process command details
        :type command_filter: string
        :param hostname: Hostname of the node to look for PID on
        :type hostname: string
        '''
        host = topology.get_openstack_node(hostname=hostname)
        processes = sh.list_processes(ssh_client=host.ssh_client)
        process = processes.with_attributes(pid=pid)
        process_destroyed = False
        if not process:
            LOG.debug(f'No PID {pid} has been found in process list')
            process_destroyed = True
        else:
            try:
                command = sh.execute(f'cat /proc/{pid}/cmdline',
                                     ssh_client=host.ssh_client)
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
        self.stopped_agent_hosts = []

    def tearDown(self):
        super(DHCPAgentTest, self).tearDown()
        # Try to start all agents which may be down during the tests
        self.start_service_on_hosts(
            self.agent_service_name, self.stopped_agent_hosts)

    def test_stop_dhcp_agent(self):
        '''Test that dnsmasq processes are not broken after DHCP agent restart

        Dnsmasq processes should stay alive if DHCP agent is turned off and
        then restarted once DHCP agent is returned to active state.
        '''
        network_dhcp_agents = neutron.list_dhcp_agent_hosting_network(
            self.stack.network)
        dhcp_agents_hosts = [agent['host'] for agent in network_dhcp_agents]
        network_dnsmasq_pids = self.get_cmd_pids("dnsmasq",
                                                 self.stack.network,
                                                 dhcp_agents_hosts)

        self.stop_service_on_hosts(self.agent_service_name, dhcp_agents_hosts)
        self.assertEqual(network_dnsmasq_pids,
                         self.get_cmd_pids("dnsmasq",
                                           self.stack.network,
                                           dhcp_agents_hosts))

        self.start_service_on_hosts(self.agent_service_name, dhcp_agents_hosts)
        self.wait_processes_destroyed(self.stack.network, network_dnsmasq_pids)
        self.get_cmd_pids("dnsmasq", self.stack.network, dhcp_agents_hosts)

    def test_dhcp_lease_served_when_dhcp_agent_down(self):
        '''Test that DHCP lease is correctly served when DHCP agent is down

        Make sure that the VM will receive IP address after the reboot.
        DHCP agent should be down during the VM reboot. VM should receive
        the same IP address that was assigned to it before the reboot.
        '''
        ping.ping_until_received(self.stack.ip_address).assert_replied()

        network_dhcp_agents = neutron.list_dhcp_agent_hosting_network(
            self.stack.network)
        dhcp_agents_hosts = [agent['host'] for agent in network_dhcp_agents]
        network_dnsmasq_pids = self.get_cmd_pids("dnsmasq",
                                                 self.stack.network,
                                                 dhcp_agents_hosts)
        self.stop_service_on_hosts(self.agent_service_name, dhcp_agents_hosts)

        nova.shutoff_server(self.stack.resources.server.physical_resource_id)
        nova.activate_server(self.stack.resources.server.physical_resource_id)
        ping.ping_until_received(self.stack.ip_address).assert_replied()

        self.start_service_on_hosts(self.agent_service_name, dhcp_agents_hosts)
        self.wait_processes_destroyed(self.stack.network, network_dnsmasq_pids)
        self.get_cmd_pids("dnsmasq", self.stack.network, dhcp_agents_hosts)


class L3AgentTest(testtools.TestCase, AgentTestMixin):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosPeerServerStackFixture)
    ha_stack = tobiko.required_setup_fixture(stacks.L3haServerStackFixture)

    def setUp(self):
        super(L3AgentTest, self).setUp()
        os_topology = topology.get_openstack_topology()
        self.agent_service_name = os_topology.get_agent_service_name(
            "neutron-l3-agent")
        if not self.agent_service_name:
            self.skip("Neutron L3 agent's service name not defined for "
                      "the topology %s" % os_topology)
        self.router_id = self.stack.network_stack.gateway_id
        self.stopped_agent_hosts = []

    def tearDown(self):
        super(L3AgentTest, self).tearDown()
        # Try to start all agents which may be down during the tests
        self.start_service_on_hosts(
            self.agent_service_name, self.stopped_agent_hosts)

    def wait_for_active_ha_l3_agent(self):
        ha_router_id = self.ha_stack.network_stack.gateway_id
        retry = tobiko.retry(timeout=60, interval=2)
        for _ in retry:
            l3_agents = neutron.list_l3_agent_hosting_routers(ha_router_id)
            if len(l3_agents.with_items(ha_state='active')) == 1:
                return l3_agents

    @neutron.skip_if_missing_networking_extensions('l3-ha')
    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_keepalived_after_l3_agent_restart(self):
        """Verifies that keepalived survives restart of L3 agents

        Keepalived should keep the same process IDs after L3 agents have been
        restarted
        """
        ha_router_id = self.ha_stack.network_stack.gateway_id
        l3_agents = self.wait_for_active_ha_l3_agent()
        l3_agents_hosts = [agent['host'] for agent in l3_agents]
        keepalived_pids = self.get_cmd_pids('keepalived',
                                            ha_router_id,
                                            l3_agents_hosts,
                                            min_pids_per_host=2)
        self.stop_service_on_hosts(self.agent_service_name, l3_agents_hosts)
        self.start_service_on_hosts(self.agent_service_name, l3_agents_hosts)
        new_agents = self.wait_for_active_ha_l3_agent()
        new_agents_hosts = [agent['host'] for agent in new_agents]
        self.assertEqual(keepalived_pids,
                         self.get_cmd_pids('keepalived',
                                           ha_router_id,
                                           new_agents_hosts,
                                           min_pids_per_host=2))

    @neutron.skip_if_missing_networking_extensions('l3-ha')
    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_keepalived_failover(self):
        ha_router_id = self.ha_stack.network_stack.gateway_id
        l3_agents = self.wait_for_active_ha_l3_agent()
        l3_agents_hosts = [agent['host'] for agent in l3_agents]
        keepalived_pids = self.get_cmd_pids('keepalived',
                                            ha_router_id,
                                            l3_agents_hosts,
                                            min_pids_per_host=2)
        ping.ping_until_received(self.ha_stack.ip_address).assert_replied()
        active_agent_host = l3_agents.with_items(ha_state='active')[0]['host']
        # Need to make sure that 'keepalived-state-change' process is UP
        # before we will kill 'keepalived' process as it can break the agent
        # status otherwise. So will check that keepalived pids are equal for
        # two attemts of listing them
        ka_state_cmd = f'neutron-keepalived-state-change.*{ha_router_id}'
        retry = tobiko.retry(timeout=120, interval=2)
        ka_state_pids = {}
        for _ in retry:
            equal = True
            new_ka_state_pids = self.get_cmd_pids('/usr/bin/python',
                                                  ka_state_cmd,
                                                  l3_agents_hosts,
                                                  min_pids_per_host=2)
            for host, pids in new_ka_state_pids.items():
                if host not in ka_state_pids:
                    equal = False
                else:
                    if pids.sort() != ka_state_pids[host].sort():
                        equal = False
            if equal:
                break
            else:
                ka_state_pids = new_ka_state_pids
        self.kill_pids(active_agent_host, keepalived_pids[active_agent_host])
        ping.ping_until_received(self.ha_stack.ip_address).assert_replied()
        # Need to make sure that 'keepalived' is spawned back after it has
        # been killed
        self.get_cmd_pids('keepalived',
                          ha_router_id,
                          l3_agents_hosts,
                          min_pids_per_host=2)

    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_metadata_haproxy_during_stop_L3_agent(self):
        network_l3_agents = neutron.list_l3_agent_hosting_routers(
            self.router_id)
        l3_agents_hosts = [agent['host'] for agent in network_l3_agents]
        router_haproxy_pids = self.get_cmd_pids("haproxy",
                                                self.router_id,
                                                l3_agents_hosts)
        self.stop_service_on_hosts(self.agent_service_name, l3_agents_hosts)
        # Now check if haproxy processes are still run and have got same pids
        # like before dhcp agent's stop
        self.assertEqual(router_haproxy_pids,
                         self.get_cmd_pids("haproxy",
                                           self.router_id,
                                           l3_agents_hosts))

        self.start_service_on_hosts(self.agent_service_name, l3_agents_hosts)

        # And finally check if haproxy processes are still run and have got
        # same pids like at the beginning of the test
        self.assertEqual(router_haproxy_pids,
                         self.get_cmd_pids("haproxy",
                                           self.router_id,
                                           l3_agents_hosts))

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
        os_topology = topology.get_openstack_topology()
        if os_topology.has_containers:
            self.skip("Radvd process is currently run directly in "
                      "neutron-l3-agent container so it will be always killed "
                      "when neutron-l3-agent container is killed and this "
                      "test is not needed")

        if not self._is_radvd_process_expected():
            self.skip("Radvd process is not expected to be run on router %s" %
                      self.router_id)

        network_l3_agents = neutron.list_l3_agent_hosting_routers(
            self.router_id)
        l3_agents_hosts = [agent['host'] for agent in network_l3_agents]
        router_radvd_pids = self.get_cmd_pids("radvd",
                                              self.router_id,
                                              l3_agents_hosts)
        self.stop_service_on_hosts(self.agent_service_name, l3_agents_hosts)
        # Now check if radvd processes are still run and have got same pids
        # like before dhcp agent's stop
        self.assertEqual(router_radvd_pids,
                         self.get_cmd_pids("radvd",
                                           self.router_id,
                                           l3_agents_hosts))

        self.start_service_on_hosts(self.agent_service_name, l3_agents_hosts)

        # And finally check if dnsmasq processes are still run and have got
        # same pids like at the beginning of the test
        self.assertEqual(router_radvd_pids,
                         self.get_cmd_pids("radvd",
                                           self.router_id,
                                           l3_agents_hosts))


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

        self.stopped_agent_hosts = []

    def tearDown(self):
        super(OvsAgentTest, self).tearDown()
        # Try to start all agents which may be down during the tests
        self.start_service_on_hosts(
            self.agent_service_name, self.stopped_agent_hosts)

    def _get_agent_from_host(self, host):
        host_shortname = tobiko.get_short_hostname(host.name)
        for agent in self.ovs_agents:
            if host_shortname == tobiko.get_short_hostname(agent['host']):
                return agent
        raise neutron.AgentNotFoundOnHost(agent_type="neutron-ovs-agent",
                                          host=host.name)

    def test_vm_reachability_during_stop_ovs_agent(self):
        # Check if vm is reachable before test
        ping.ping_until_received(self.stack.ip_address).assert_replied()

        vm_host = topology.get_openstack_node(
            hostname=self.stack.hypervisor_host)
        agent = self._get_agent_from_host(vm_host)
        self.stop_service_on_hosts(self.agent_service_name, [agent['host']])
        ping.ping_until_received(
            self.stack.floating_ip_address).assert_replied()
        self.start_service_on_hosts(self.agent_service_name, [agent['host']])


class MetadataAgentTest(testtools.TestCase, AgentTestMixin):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def setUp(self):
        super(MetadataAgentTest, self).setUp()
        os_topology = topology.get_openstack_topology()
        self.agent_service_name = os_topology.get_agent_service_name(
            "neutron-metadata-agent")
        if not self.agent_service_name:
            self.skip("Neutron metadata agent's service name not defined for "
                      "the topology %s" % os_topology)
        self.stopped_agent_hosts = []

    def tearDown(self):
        super(MetadataAgentTest, self).tearDown()
        # Try to start all agents which may be down during the tests
        self.start_service_on_hosts(
            self.agent_service_name, self.stopped_agent_hosts)

    def is_metadata_reachable(self):
        """Test if metadata agent is acting as proxy to nova metadata

        Expected resonse code from metadata agent is "HTTP/1.1 200 OK"
        if the agent is working. "HTTP/1.0 503 Service Unavailable" otherwise.
        All other response codes are not expected.
        """
        curl_output = sh.execute(
                'curl http://169.254.169.254/latest/meta-data/ -I',
                ssh_client=self.stack.ssh_client,
                expect_exit_status=None).stdout.strip()
        LOG.debug(f'Metadata return: \n{curl_output}')
        http_status = curl_output.split('\n')[0].split(' ')[1]
        if http_status == '200':
            return True
        elif http_status == '503':
            return False
        else:
            self.fail(f'Unexpected HTTP status {http_status}')

    def wait_metadata_reachable(self, timeout=60, interval=2):
        retry = tobiko.retry(timeout=timeout, interval=interval)
        for _ in retry:
            if self.is_metadata_reachable():
                return True

    def test_metadata_restart(self):
        agents = neutron.list_agents(agent_type='Metadata agent')
        hosts = [agent['host'] for agent in agents]
        LOG.debug('Test if metadata agent is reachable before the test')
        self.assertTrue(self.is_metadata_reachable())
        LOG.debug('Try to stop metadata agent on all the nodes')
        self.stop_service_on_hosts(self.agent_service_name, hosts)
        LOG.debug('Test if metadata agent is not reachable after it stopped')
        self.assertFalse(self.is_metadata_reachable())
        LOG.debug('Try to start metadata agent on all the nodes')
        self.start_service_on_hosts(self.agent_service_name, hosts)
        LOG.debug('Test if metadata agent is reachable after restart')
        self.assertTrue(self.wait_metadata_reachable())
