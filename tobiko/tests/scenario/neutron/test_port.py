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

import json
import typing

import netaddr
from oslo_log import log
import testtools

import tobiko
from tobiko.shell import ping
from tobiko.shell import ip
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.openstack import topology


LOG = log.getLogger(__name__)


class PortTest(testtools.TestCase):
    """Test Neutron ports"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def test_port_ips(self, ip_version: typing.Optional[int] = None):
        """Checks port IPS has been assigned to server via DHCP protocol"""
        port_ips = set(neutron.list_device_ip_addresses(
            device_id=self.stack.server_id,
            network_id=self.stack.network_stack.network_id,
            need_dhcp=self.stack.need_dhcp,
            ip_version=ip_version))
        if port_ips:
            # verify neutron port IPs and VM port IPs match
            # when a VM connected to the external network has been just
            # created, it may need some time to receive its IPv6 address
            for attempt in tobiko.retry(timeout=60., interval=4.):
                server_ips = set(ip.list_ip_addresses(
                    scope='global', ssh_client=self.stack.ssh_client))
                server_ips &= port_ips  # ignore other server IPs
                LOG.debug("Neutron IPs and VM IPs should match...")
                try:
                    self.assertEqual(
                        port_ips, server_ips,
                        f"Server {self.stack.server_id} is missing port "
                        f"IP(s): {port_ips - server_ips}")
                    break
                except self.failureException:
                    attempt.check_limits()
        elif ip_version:
            self.skipTest(f"Server has any port IPv{ip_version} address to be"
                          " tested")
        else:
            self.skipTest("Server has any port IP address to be tested")

    def test_port_network(self):
        self.assertEqual(self.stack.network_stack.network_id,
                         self.stack.port_details['network_id'])

    def test_port_subnets(self):
        """Checks port subnets"""
        port_subnets = [fixed_ip['subnet_id']
                        for fixed_ip in self.stack.port_details['fixed_ips']]
        network_subnets = self.stack.network_stack.network_details['subnets']
        self.assertEqual(set(network_subnets), set(port_subnets))

    def test_ping_subnet_gateways(self):
        """Checks server can ping its gateway IPs"""
        network_id = self.stack.network_stack.network_id
        subnets = neutron.list_subnets(network_id=network_id)
        LOG.debug("Subnets enabled are:\n"
                  f"{json.dumps(subnets, indent=4, sort_keys=True)}")
        gateway_ips = [netaddr.IPAddress(subnet['gateway_ip'])
                       for subnet in subnets]
        LOG.debug(f"Gateway IPs are: {gateway_ips}")
        ping.assert_reachable_hosts(gateway_ips,
                                    ssh_client=self.stack.ssh_client)

    def test_ping_port(self, network_id=None, device_id=None, ip_version=None):
        """Checks server can ping its own port"""
        port_ips = neutron.list_device_ip_addresses(
            device_id=device_id or self.stack.server_id,
            network_id=network_id or self.stack.network_stack.network_id,
            need_dhcp=self.stack.need_dhcp,
            ip_version=ip_version)
        if port_ips:
            ping.assert_reachable_hosts(port_ips,
                                        timeout=600.,
                                        ssh_client=self.stack.peer_ssh_client)
        elif ip_version:
            self.skipTest(f"Server has any port IPv{ip_version} address to be"
                          " tested")
        else:
            self.skipTest("Server has any port IP address to be tested")


# --- Test opening ports on external network ----------------------------------

@stacks.skip_unless_has_external_network
class UbuntuExternalPortTest(PortTest):
    """Test Neutron ports"""

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_setup_fixture(
        stacks.UbuntuExternalServerStackFixture)


# --- Test la-h3 extension ----------------------------------------------------

@neutron.skip_if_missing_networking_extensions('l3-ha')
@neutron.skip_if_missing_networking_agents(binary='neutron-l3-agent',
                                           count=2)
class L3HAPortTest(PortTest):
    #: Resources stack with floating IP and Nova server
    stack = tobiko.required_setup_fixture(stacks.L3haServerStackFixture)


# --- Port events logging ----------------------------------------------------

class PortLogsStack(stacks.CirrosServerStackFixture):
    pass


@neutron.skip_unless_is_ovs()
class PortLogsTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(PortLogsStack)

    def test_nova_port_notification_on_activate(self):
        self.stack.ensure_server_status('SHUTOFF')
        topology.read_neutron_nova_responses()

        LOG.debug("Activate server")
        nova.activate_server(self.stack.server_id)
        self.assert_last_response(name='network-vif-plugged',
                                  new_lines=True)

    valid_response_names = frozenset(['network-vif-plugged',
                                      'network-vif-unplugged'])

    def is_valid_response(self,
                          response: topology.NeutronNovaResponse) -> bool:
        return response.name in self.valid_response_names

    def assert_last_response(self,
                             name: str,
                             new_lines: bool,
                             retry_timeout: tobiko.Seconds = None,
                             retry_interval: tobiko.Seconds = None):
        self.assertIn(name, self.valid_response_names)
        for attempt in tobiko.retry(timeout=retry_timeout,
                                    interval=retry_interval,
                                    default_timeout=60.,
                                    default_interval=1.):
            responses = topology.read_neutron_nova_responses(
                server_uuid=self.stack.server_id,
                tag=self.stack.port_id,
                status='completed',
                new_lines=new_lines).select(self.is_valid_response)
            try:
                found = responses.with_attributes(name=name).last
            except tobiko.ObjectNotFound:
                new_lines = True
                if attempt.is_last:
                    responses_text = ''.join(f'\t{r}\n' for r in responses)
                    tobiko.fail(
                        f"Nova response with name '{name}' not logged by "
                        "Neutron server:\n"
                        f"{responses_text}\n")
            else:
                break
        else:
            raise RuntimeError("Broken retry loop")

        if found is responses.last:
            LOG.debug("Found expected response: "
                      f"{json.dumps(found, sort_keys=True, indent=4)}")
        else:
            responses_text = ''.join(f'\t{r}\n' for r in responses)
            tobiko.fail(f"Unexpected events found after '{name}':\n"
                        f"{responses_text}")
