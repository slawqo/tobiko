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
import typing  # noqa

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

# typing hits
AgentType = typing.Dict[str, typing.Any]
AgentListType = typing.List[AgentType]


class BaseAgentTest(testtools.TestCase):

    agent_name: str = '<undefined agent name>'

    @classmethod
    def setUpClass(cls):
        cls.service_name: str = topology.get_agent_service_name(cls.agent_name)
        cls.container_name: str = ''
        cls.agents: AgentListType = \
            neutron.list_networking_agents(binary=cls.agent_name)

    def setUp(self):
        super(BaseAgentTest, self).setUp()
        if not self.agents:
            self.skipTest(f"Missing Neutron agent(s): '{self.agent_name}'")

    @property
    def hosts(self) -> typing.List[str]:
        return [agent['host'] for agent in self.agents]

    def stop_agent(self, hosts: typing.Optional[typing.List[str]] = None):
        '''Stop network agent on hosts

        It ensures service service is stopped and register systemd service
        restart as test case cleanup. In case of systemd service is not
        available it stops the container itself

        :parm hosts: List of hostnames to stop agent on
        :type hosts: list of strings
        '''
        hosts = hosts or self.hosts
        self.assertNotEqual([], hosts, "Host list is empty")

        for host in hosts:
            ssh_client = topology.get_openstack_node(hostname=host).ssh_client
            is_systemd = topology.check_systemd_monitors_agent(host,
                                                               self.agent_name)
            if is_systemd:
                LOG.debug(f"Stopping service '{self.service_name}' on "
                          f"host '{host}'...")
                sh.execute(f"systemctl stop {self.service_name}",
                           ssh_client=ssh_client,
                           sudo=True)
                LOG.debug(f"Service '{self.service_name}' stopped on host "
                          f"'{host}'.")
            else:
                self.container_name = \
                            topology.get_agent_container_name(self.agent_name)
                LOG.debug(f'Stopping container {self.container_name} on '
                          f"host '{host}'...")
                sh.execute(f'docker stop {self.container_name}',
                           ssh_client=ssh_client,
                           sudo=True)
                LOG.debug(f'Container {self.container_name} has been stopped '
                          f"on host '{host}'...")
            # Schedule auto-restart of service at the end of this test case
            self.addCleanup(self.start_agent, hosts=[host, ])

    def start_agent(self, hosts: typing.Optional[typing.List[str]] = None):
        '''Start network agent on hosts

        It ensures system service is running. If the systemd service is not
        available it starts container itself

        :parm hosts: List of hostnames to start agent on
        :type hosts: list of strings
        '''
        hosts = hosts or self.hosts
        self.assertNotEqual([], hosts, "Host list is empty")

        for host in hosts:
            ssh_client = topology.get_openstack_node(hostname=host).ssh_client
            is_systemd = topology.check_systemd_monitors_agent(host,
                                                               self.agent_name)
            if is_systemd:
                LOG.debug(f"Starting service '{self.service_name}' on "
                          f"host '{host}'...")
                sh.execute(f"systemctl start {self.service_name}",
                           ssh_client=ssh_client,
                           sudo=True)
            else:
                self.container_name = \
                            topology.get_agent_container_name(self.agent_name)
                LOG.debug(f'Starting container {self.container_name} on '
                          f"host '{host}'...")
                sh.execute(f'docker start {self.container_name}',
                           ssh_client=ssh_client,
                           sudo=True)

    def get_cmd_pids(self, process_name, command_filter, hosts=None,
                     timeout=120, interval=2, min_pids_per_host=1) -> \
            typing.Dict[str, frozenset]:
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
        hosts = hosts or self.hosts
        self.assertNotEqual([], hosts, "Host list is empty")

        pids_per_host = {}
        for host in hosts:
            LOG.debug(f'Search for {process_name} process on {host}')
            retry = tobiko.retry(timeout=timeout, interval=interval)
            for _ in retry:
                pids = self.list_pids(host, command_filter, process_name)
                if len(pids) >= min_pids_per_host:
                    pids_per_host[host] = frozenset(pids)
                    LOG.debug(f"Process '{process_name}' is running "
                              f"on host '{host}' (PIDs={pids!r})")
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


class DHCPAgentTest(BaseAgentTest):

    agent_name = neutron.DHCP_AGENT

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def test_stop_dhcp_agent(self):
        '''Test that dnsmasq processes are not broken after DHCP agent restart

        Dnsmasq processes should stay alive if DHCP agent is turned off and
        then restarted once DHCP agent is returned to active state.
        '''
        self.agents = neutron.list_dhcp_agent_hosting_network(
            self.stack.network)
        self.assertNotEqual(
            [], self.agents, "No DHCP agent found serving network "
            f"'{self.stack.network}'")
        pids = self.get_cmd_pids("dnsmasq", self.stack.network)

        self.stop_agent()
        self.assertEqual(pids, self.get_cmd_pids("dnsmasq",
                                                 self.stack.network))

        self.start_agent()
        self.wait_processes_destroyed(self.stack.network, pids)
        new_pids = self.get_cmd_pids("dnsmasq", self.stack.network)
        self.assertNotEqual(pids, new_pids)

    def test_dhcp_lease_served_when_dhcp_agent_down(self):
        '''Test that DHCP lease is correctly served when DHCP agent is down

        Make sure that the VM will receive IP address after the reboot.
        DHCP agent should be down during the VM reboot. VM should receive
        the same IP address that was assigned to it before the reboot.
        '''
        ping.ping_until_received(self.stack.ip_address).assert_replied()

        self.agents = neutron.list_dhcp_agent_hosting_network(
            self.stack.network)
        self.assertNotEqual(
            [], self.agents, "No DHCP agent found serving network "
            f"'{self.stack.network}'")
        pids = self.get_cmd_pids("dnsmasq", self.stack.network)
        self.stop_agent()

        nova.shutoff_server(self.stack.server_id)
        nova.activate_server(self.stack.server_id)
        ping.ping_until_received(self.stack.ip_address).assert_replied()

        self.start_agent()
        self.wait_processes_destroyed(self.stack.network, pids)
        new_pids = self.get_cmd_pids("dnsmasq", self.stack.network)
        self.assertNotEqual(pids, new_pids)


class L3AgentTest(BaseAgentTest):

    agent_name = neutron.L3_AGENT

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosPeerServerStackFixture)
    ha_stack = tobiko.required_setup_fixture(stacks.L3haServerStackFixture)

    def setUp(self):
        super(L3AgentTest, self).setUp()
        self.router_id = self.stack.network_stack.gateway_id

    def wait_for_active_ha_l3_agent(self) -> AgentType:
        ha_router_id = self.ha_stack.network_stack.gateway_id
        for attempt in tobiko.retry(timeout=180., interval=5.):
            agents = neutron.list_l3_agent_hosting_routers(ha_router_id)
            try:
                active_agent = agents.with_items(ha_state='active').unique
                break
            except (tobiko.MultipleObjectsFound, tobiko.ObjectNotFound):
                attempt.check_limits()
                continue

        return active_agent

    @neutron.skip_if_missing_networking_extensions('l3-ha')
    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_keepalived_after_l3_agent_restart(self):
        """Verifies that keepalived survives restart of L3 agents

        Keepalived should keep the same process IDs after L3 agents have been
        restarted
        """
        self.agents = [self.wait_for_active_ha_l3_agent()]
        ha_router_id = self.ha_stack.network_stack.gateway_id
        pids = self.get_cmd_pids('keepalived', ha_router_id,
                                 min_pids_per_host=2)
        self.stop_agent()
        self.start_agent()
        self.agents = [self.wait_for_active_ha_l3_agent()]
        self.assertEqual(pids,
                         self.get_cmd_pids('keepalived',
                                           ha_router_id,
                                           min_pids_per_host=2))

    @neutron.skip_if_missing_networking_extensions('l3-ha')
    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_keepalived_failover(self):
        ha_router_id = self.ha_stack.network_stack.gateway_id
        self.agents = [self.wait_for_active_ha_l3_agent()]
        keepalived_pids = self.get_cmd_pids('keepalived',
                                            ha_router_id,
                                            min_pids_per_host=2)
        ping.ping_until_received(self.ha_stack.ip_address).assert_replied()
        active_agent_host = self.agents[0]['host']

        # Need to make sure that 'keepalived-state-change' process is UP
        # before we will kill 'keepalived' process as it can break the agent
        # status otherwise. So will check that keepalived pids are equal for
        # two attemts of listing them
        ka_state_cmd = f'neutron-keepalived-state-change.*{ha_router_id}'
        ka_state_pids = {}
        for _ in tobiko.retry(timeout=120., interval=5.):
            new_ka_state_pids = self.get_cmd_pids('/usr/bin/python',
                                                  ka_state_cmd,
                                                  min_pids_per_host=1)
            if ka_state_pids == new_ka_state_pids:
                break
            else:
                ka_state_pids = new_ka_state_pids

        self.kill_pids(active_agent_host, keepalived_pids[active_agent_host])
        ping.ping_until_received(self.ha_stack.ip_address).assert_replied()

        # Need to make sure that 'keepalived' is spawned back after it has
        # been killed
        self.assertNotEqual(keepalived_pids,
                            self.get_cmd_pids('keepalived',
                                              ha_router_id,
                                              min_pids_per_host=2))

    @neutron.skip_if_missing_networking_extensions('l3_agent_scheduler')
    def test_metadata_haproxy_during_stop_L3_agent(self):
        self.agents = neutron.list_l3_agent_hosting_routers(self.router_id)
        pids = self.get_cmd_pids("haproxy", self.router_id)
        self.stop_agent()

        # Now check if haproxy processes are still run and have got same pids
        # like before dhcp agent's stop
        self.assertEqual(pids, self.get_cmd_pids("haproxy", self.router_id))

        self.start_agent()

        # And finally check if haproxy processes are still run and have got
        # same pids like at the beginning of the test
        self.assertEqual(pids, self.get_cmd_pids("haproxy", self.router_id))

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

        self.agents = neutron.list_l3_agent_hosting_routers(self.router_id)
        pids = self.get_cmd_pids("radvd", self.router_id)
        self.stop_agent()
        # Now check if radvd processes are still run and have got same pids
        # like before dhcp agent's stop
        self.assertEqual(pids, self.get_cmd_pids("radvd", self.router_id))

        self.start_agent()

        # And finally check if dnsmasq processes are still run and have got
        # same pids like at the beginning of the test
        self.assertEqual(pids, self.get_cmd_pids("radvd", self.router_id))


class OpenVSwitchAgentTest(BaseAgentTest):

    agent_name = neutron.OPENVSWITCH_AGENT

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def get_agent_from_host(self, hypervisor_host):
        # pylint: disable=not-an-iterable
        short_name = tobiko.get_short_hostname(hypervisor_host)
        for agent in self.agents:
            if short_name == tobiko.get_short_hostname(agent['host']):
                return agent
        raise neutron.AgentNotFoundOnHost(agent_type=neutron.OPENVSWITCH_AGENT,
                                          host=hypervisor_host)

    def test_vm_reachability_during_stop_ovs_agent(self):
        # Check if vm is reachable before stopping service
        self.start_agent()
        ping.ping_until_received(self.stack.ip_address).assert_replied()

        # Check if vm is reachable after stopping service
        self.stop_agent(hosts=[self.stack.hypervisor_host])
        ping.ping_until_received(self.stack.ip_address).assert_replied()


# TODO(eolivare): these tests will always be skipped on OSP13 because 'agent
# list' requests return empty list with OVN+OSP13
# Search for the corresponding container instead of the networking agent
class OvnControllerTest(BaseAgentTest):

    agent_name = neutron.OVN_CONTROLLER

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def test_restart_ovn_controller(self):
        '''Test that OVN controller agents can be restarted successfully
        '''
        self.stop_agent()
        ping.ping_until_received(self.stack.ip_address).assert_replied()

        self.start_agent()
        ping.ping_until_received(self.stack.ip_address).assert_replied()


class MetadataAgentTest(BaseAgentTest):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    agent_name = neutron.METADATA_AGENT

    def wait_for_metadata_status(self, count=None, timeout=60., interval=2.,
                                 is_reachable: typing.Optional[bool] = None):
        for attempt in tobiko.retry(timeout=timeout, interval=interval,
                                    count=count):
            if is_reachable is not None:
                try:
                    self.assert_metadata_is_reachable(is_reachable)
                except self.failureException:
                    # re-raises failureException when reaching retry limits
                    attempt.check_limits()
                else:
                    break

    def assert_metadata_is_reachable(self, is_reachable: bool,
                                     metadata_url: str = None):
        """Test if metadata agent is acting as proxy to nova metadata

        Expected response code from metadata agent is "HTTP/1.1 200 OK"
        if the agent is working. "HTTP/1.0 503 Service Unavailable" or
        exit_status=7 otherwise.
        All other HTTP statuses and exit codes are considered failures.
        """
        if is_reachable not in [True, False]:
            raise TypeError("'is_reachable' parameter is not a bool: "
                            f"{is_reachable!r}")
        # TODO: fix hard coded IP address
        metadata_url = (metadata_url or
                        'http://169.254.169.254/latest/meta-data/')

        try:
            result = sh.execute(f"curl '{metadata_url}' -I",
                                ssh_client=self.stack.ssh_client)
        except sh.ShellCommandFailed as ex:
            # Cant reach the server
            self.assertFalse(is_reachable,
                             "Metadata server not reached from Nova server:\n"
                             f"exit_status={ex.exit_status}\n"
                             f"{ex.stderr}")
            self.assertEqual(7, ex.exit_status,
                             f"Unexpected Curl exit status: {ex.exit_status}\n"
                             f"{ex.stderr}")
        else:
            # Command has succeeded, let parse the HTTP status
            curl_output = result.stdout.strip()
            LOG.debug(f"Remote HTTP server replied:\n{curl_output}")
            http_status = parse_http_status(curl_output=curl_output)
            if is_reachable:
                self.assertEqual(
                    200, http_status,
                    "Metadata server not reached from Nova server:\n"
                    f"{curl_output}")
            else:
                self.assertEqual(
                    503, http_status,
                    "Metadata server reached from Nova server:\n"
                    f"{curl_output}")

    def test_metadata_service_restart(self):
        # Ensure service is up
        self.start_agent()
        self.wait_for_metadata_status(is_reachable=True)

        # Ensure the servive gets down
        self.stop_agent()
        self.wait_for_metadata_status(is_reachable=False)

        # Ensure service gets up again
        self.start_agent()
        self.wait_for_metadata_status(is_reachable=True)

    def test_vm_reachability_when_metadata_agent_is_down(self):
        self.stop_agent()
        self.wait_for_metadata_status(is_reachable=False)
        ping.ping_until_received(self.stack.ip_address).assert_replied()
        self.start_agent()
        self.wait_for_metadata_status(is_reachable=True)


# TODO(eolivare): these tests will always be skipped on OSP13 because 'agent
# list' requests return empty list with OVN+OSP13
# Search for the corresponding container instead of the networking agent
class OvnMetadataAgentTest(MetadataAgentTest):

    agent_name = neutron.OVN_METADATA_AGENT


def parse_http_status(curl_output: str) -> int:
    http_head = curl_output.split('\n', 1)[0]
    return int(http_head.split(' ', 2)[1])