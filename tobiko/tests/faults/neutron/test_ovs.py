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

import collections

import testtools

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import stacks
from tobiko.openstack import topology
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.tripleo import undercloud


@neutron.skip_if_missing_networking_agents(neutron.OPENVSWITCH_AGENT)
@neutron.skip_if_missing_networking_agents(neutron.L3_AGENT)
class OpenvswitchTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)

    def setUp(self):
        super(OpenvswitchTest, self).setUp()
        self.ovs_agents = neutron.list_agents(agent_type="Open vSwitch agent")
        self.router_id = self.stack.network_stack.gateway_id

        self.deleted_bridges = collections.defaultdict(set)

    def tearDown(self):
        super(OpenvswitchTest, self).tearDown()
        # Try to create all bridges which were deleted during the tests
        self._create_bridges()

    def _create_bridges(self):
        for host, bridges in self.deleted_bridges.items():
            self._create_bridge(host, bridges)

    def _create_bridge(self, hostname, bridges):
        for br_name in bridges:
            agent_host = topology.get_openstack_node(hostname=hostname)
            sh.execute(
                "sudo ovs-vsctl --may-exist add-br %s" % br_name,
                ssh_client=agent_host.ssh_client)

    def _delete_bridges(self, hostname, bridges):
        for br_name in bridges:
            agent_host = topology.get_openstack_node(hostname=hostname)
            sh.execute(
                "sudo ovs-vsctl del-br %s" % br_name,
                ssh_client=agent_host.ssh_client)
            self.deleted_bridges[hostname].add(br_name)

    def _get_agent_from_host(self, hostname):
        host_shortname = tobiko.get_short_hostname(hostname)
        for agent in self.ovs_agents:
            if host_shortname == tobiko.get_short_hostname(agent['host']):
                return agent
        raise neutron.AgentNotFoundOnHost(agent_type="neutron-ovs-agent",
                                          host=hostname)

    @undercloud.skip_if_missing_undercloud
    def test_recreate_physical_bridge(self):
        # Check if vm is reachable before test
        ip_add = self.stack.ip_address
        ping.ping_until_received(ip_add).assert_replied()

        network_l3_agents = neutron.list_l3_agent_hosting_routers(
            self.router_id)
        for agent in network_l3_agents:
            # Get neutron-ovs-agent bridge mappings
            ovs_agent = self._get_agent_from_host(agent['host'])
            self._delete_bridges(
                agent['host'],
                ovs_agent['configurations']['bridge_mappings'].values())

        ping.ping_until_unreceived(ip_add).assert_not_replied()
        self._create_bridges()
        ping.ping_until_received(ip_add).assert_replied()
