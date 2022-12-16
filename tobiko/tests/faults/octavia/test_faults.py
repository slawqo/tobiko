# Copyright (c) 2021 Red Hat
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
from oslo_log import log

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import octavia
from tobiko.openstack import stacks
from tobiko.shell import ssh
from tobiko.shell import sh
from tobiko import tripleo


LOG = log.getLogger(__name__)


@keystone.skip_if_missing_service(name='octavia')
@tripleo.skip_if_missing_overcloud
class OctaviaBasicFaultTest(testtools.TestCase):
    """Octavia fault scenario test.

    Create a load balancer with 2 members that run a server application,
    Create a client that is connected to the load balancer VIP port,
    Generate network traffic from the client to the load balanacer VIP.
    Restart the amphora's compute node to create a failover.
    Reach the members to make sure they are ready to be checked.
    Generate network traffic again to verify Octavia functionality.
    """
    loadbalancer_stack = tobiko.required_fixture(
        stacks.AmphoraIPv4LoadBalancerStack)

    listener_stack = tobiko.required_fixture(
        stacks.HttpRoundRobinAmphoraIpv4Listener)

    def setUp(self):
        # pylint: disable=no-member
        super(OctaviaBasicFaultTest, self).setUp()

        # Wait for Octavia objects to be active
        LOG.info('Waiting for member '
                 f'{self.listener_stack.server_stack.stack_name} and '
                 f'for member '
                 f'{self.listener_stack.other_server_stack.stack_name} '
                 f'to be created...')
        self.listener_stack.wait_for_active_members()

        self.loadbalancer_stack.wait_for_octavia_service()

        self.listener_stack.wait_for_members_to_be_reachable()

        # For 5 minutes we ignore specific exceptions as we know
        # that Octavia resources are being provisioned
        for attempt in tobiko.retry(timeout=300.):
            try:
                octavia.check_members_balanced(
                    pool_id=self.listener_stack.pool_id,
                    ip_address=self.loadbalancer_stack.floating_ip_address,
                    lb_algorithm=self.listener_stack.lb_algorithm,
                    protocol=self.listener_stack.lb_protocol,
                    port=self.listener_stack.lb_port)
                break
            except (octavia.RoundRobinException,
                    octavia.TrafficTimeoutError,
                    sh.ShellCommandFailed):
                LOG.exception(f"Traffic didn't reach all members after "
                              f"#{attempt.number} attempts and "
                              f"{attempt.elapsed_time} seconds")
                if attempt.is_last:
                    raise

    @property
    def amphora_ssh_client(self) -> ssh.SSHClientType:
        return self.listener_stack.amphora_ssh_client

    def test_reboot_amphora_compute_node(self):
        amphora_compute_host = octavia.get_amphora_compute_node(
            load_balancer=self.loadbalancer_stack.loadbalancer_id,
            port=self.listener_stack.lb_port,
            protocol=self.listener_stack.lb_protocol,
            ip_address=self.loadbalancer_stack.floating_ip_address)

        LOG.debug('Rebooting compute node...')

        # Reboot Amphora's compute node will initiate a failover
        amphora_compute_host.reboot_overcloud_node()

        LOG.debug('Compute node has been rebooted')

        # Wait for the LB to be updated
        try:
            self.loadbalancer_stack.wait_for_update_loadbalancer(timeout=30)

        except tobiko.RetryTimeLimitError:
            LOG.info('The restarted servers reached ACTIVE status after the'
                     ' LB finished its update process, hence no exception is'
                     ' being raised even though the update timeout was'
                     ' reached.')

        self.loadbalancer_stack.wait_for_active_loadbalancer()

        LOG.debug(f'Load Balancer {self.loadbalancer_stack.loadbalancer_id} is'
                  f' ACTIVE')

        # Wait for Octavia objects' provisioning status to be ACTIVE
        self.listener_stack.wait_for_active_members()

        # Verify Octavia functionality
        # For 5 minutes we ignore specific exceptions as we know
        # that Octavia resources are being provisioned/migrated
        for attempt in tobiko.retry(timeout=300.):
            try:
                octavia.check_members_balanced(
                    pool_id=self.listener_stack.pool_id,
                    ip_address=self.loadbalancer_stack.floating_ip_address,
                    lb_algorithm=self.listener_stack.lb_algorithm,
                    protocol=self.listener_stack.lb_protocol,
                    port=self.listener_stack.lb_port)
                break
            except (octavia.RoundRobinException,
                    octavia.TrafficTimeoutError,
                    sh.ShellCommandFailed):
                LOG.exception(f"Traffic didn't reach all members after "
                              f"#{attempt.number} attempts and "
                              f"{attempt.elapsed_time} seconds")
                if attempt.is_last:
                    raise

    def test_kill_amphora_agent(self):
        """Kill the MASTER amphora agent

        This test kills the amphora agent on the MASTER amphora.
        Killing the amphora agent will cause a failover.

        Octavia's functionality will be verified afterwards.
        """

        self._skip_if_not_active_standby()

        # Finding the amphora agent pid and kill it
        amp_agent_pid_command = (
            "ps -ef | awk '/amphora/{print $2}' | head -n 1")
        amp_agent_pid = octavia.run_command_on_amphora(
            command=amp_agent_pid_command,
            lb_id=self.loadbalancer_stack.loadbalancer_id,
            lb_fip=self.loadbalancer_stack.floating_ip_address)
        LOG.info(f'The amp_agent_pid is {amp_agent_pid}')

        octavia.run_command_on_amphora(
            command=f'kill -9 {amp_agent_pid}',
            lb_id=self.loadbalancer_stack.loadbalancer_id,
            lb_fip=self.loadbalancer_stack.floating_ip_address,
            sudo=True)

        self._wait_for_failover_and_test_functionality()

    def test_stop_keepalived(self):
        """Stop keepalived on MASTER amphora

        This test stops keepalived on the MASTER amphora.
        Stopping keepalived on the amphora will cause a failover.

        Octavia's functionality will be verified afterwards.
        """

        self._skip_if_not_active_standby()

        stop_keepalived_cmd = 'systemctl stop octavia-keepalived'

        octavia.run_command_on_amphora(
            command=stop_keepalived_cmd,
            lb_id=self.loadbalancer_stack.loadbalancer_id,
            lb_fip=self.loadbalancer_stack.floating_ip_address,
            sudo=True)

        self._wait_for_failover_and_test_functionality()

    def test_stop_haproxy(self):
        """Stop haproxy on MASTER amphora

        This test stops haproxy on the MASTER amphora.
        Stopping haproxy on the amphora will cause a failover.

        Octavia's functionality will be verified afterwards.
        """

        self._skip_if_not_active_standby()

        # Finding the amphora haproxy unit name and stop it
        amp_haproxy_unit_command = (
            "systemctl list-units | awk '/haproxy-/{print $1}'")
        amp_haproxy_unit = octavia.run_command_on_amphora(
            command=amp_haproxy_unit_command,
            lb_id=self.loadbalancer_stack.loadbalancer_id,
            lb_fip=self.loadbalancer_stack.floating_ip_address)
        LOG.info(f'The amp_haproxy_unit is {amp_haproxy_unit}')

        octavia.run_command_on_amphora(
            command=f'systemctl stop {amp_haproxy_unit}',
            lb_id=self.loadbalancer_stack.loadbalancer_id,
            lb_fip=self.loadbalancer_stack.floating_ip_address,
            sudo=True)

        self._wait_for_failover_and_test_functionality()

    def _skip_if_not_active_standby(self):
        """Skip the test if Octavia doesn't use Active/standby topology
        """
        if len(octavia.list_amphorae(
                self.loadbalancer_stack.loadbalancer_id)) < 2:
            skipping_stmt = 'Skipping the test as it requires ' \
                            'Active/standby topology.'
            LOG.info(skipping_stmt)
            self.skipTest(skipping_stmt)

    def _wait_for_failover_and_test_functionality(self):
        """Wait for failover to end and test Octavia functionality"""

        self.loadbalancer_stack.wait_for_update_loadbalancer()
        self.loadbalancer_stack.wait_for_active_loadbalancer()

        LOG.debug(f'Load Balancer {self.loadbalancer_stack.loadbalancer_id} is'
                  f' ACTIVE')

        # Wait for Octavia objects' provisioning status to be ACTIVE
        self.listener_stack.wait_for_active_members()

        # For 5 minutes we ignore specific exceptions as we know
        # that Octavia resources are being reprovisioned (amphora during a
        # failover)
        for attempt in tobiko.retry(timeout=300.):
            try:
                octavia.check_members_balanced(
                    pool_id=self.listener_stack.pool_id,
                    ip_address=self.loadbalancer_stack.floating_ip_address,
                    lb_algorithm=self.listener_stack.lb_algorithm,
                    protocol=self.listener_stack.lb_protocol,
                    port=self.listener_stack.lb_port)
                break
            except octavia.RoundRobinException:
                LOG.exception(f"Traffic didn't reach all members after "
                              f"#{attempt.number} attempts and "
                              f"{attempt.elapsed_time} seconds")
                if attempt.is_last:
                    raise
