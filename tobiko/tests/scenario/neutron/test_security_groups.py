# Copyright (c) 2023 Red Hat
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

from oslo_log import log
import testtools

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import stacks
from tobiko.openstack import topology
from tobiko.shell import sh
from tobiko.tripleo import containers
from tobiko.tripleo import overcloud

LOG = log.getLogger(__name__)


class BaseSecurityGroupTest(testtools.TestCase):

    #: Resources stack with Nova server to send messages to
    stack = tobiko.required_fixture(
        stacks.CirrosServerWithDefaultSecurityGroupStackFixture)

    _ovn_nb_db = None
    _host_ssh_client = None
    _container_runtime_name = None
    _container_name = None

    def setUp(self):
        super(BaseSecurityGroupTest, self).setUp()
        self.ovn_controller_agents = neutron.list_networking_agents(
            binary=neutron.OVN_CONTROLLER)
        if len(self.ovn_controller_agents) < 1:
            self.skip(f"No running {neutron.OVN_CONTROLLER} agents found. "
                      f"Stateless Security Group tests requires ML2/OVN "
                      f"deployment.")

    @property
    def ovn_nb_db(self):
        if not self._ovn_nb_db:
            command_result = sh.execute(
                "ovs-vsctl get open . external_ids:ovn-remote | "
                "sed -e 's/\"//g' | sed 's/6642/6641/g'",
                ssh_client=self.host_ssh_client,
                sudo=True)
            self._ovn_nb_db = command_result.stdout
        return self._ovn_nb_db

    @property
    def host_ssh_client(self):
        if not self._host_ssh_client:
            self._host_ssh_client = topology.get_openstack_node(
                hostname=self.ovn_controller_agents[0]['host']).ssh_client
        return self._host_ssh_client

    @property
    def container_runtime_name(self):
        if not self._container_runtime_name:
            if overcloud.has_overcloud():
                self._container_runtime_name = (
                    containers.get_container_runtime_name())
            else:
                self._container_runtime_name = 'docker'
        return self._container_runtime_name

    @property
    def container_name(self):
        if self._container_name is None:
            os_topology = topology.get_openstack_topology()
            if os_topology.has_containers:
                self._container_name = topology.get_agent_container_name(
                    neutron.OVN_CONTROLLER
                )
            else:
                self._container_name = ""
        return self._container_name

    def _check_sg_rule_in_ovn_nb_db(self, rule_id: str, expected_action: str):
        os_topology = topology.get_openstack_topology()
        command = ""
        if os_topology.has_containers:
            command += (
                f"{self.container_runtime_name} exec {self.container_name} ")
        command += (
            f"ovn-nbctl --format json --no-leader-only --db={self.ovn_nb_db} "
            f"find ACL external_ids:\"neutron\\:security_group_rule_id\"="
            f"\"{rule_id}\""
        )
        command_result = sh.execute(
            command, ssh_client=self.host_ssh_client, sudo=True)
        acl_rule = json.loads(command_result.stdout)
        self._assert_acl_action(acl_rule, expected_action)

    def _assert_acl_action(self, acl: dict, expected_action: str):
        action_column = acl['headings'].index('action')
        self.assertEqual(
            expected_action,
            acl['data'][0][action_column])

    def _check_sg_rules_in_ovn_nb_db(self, sg: dict, expected_action: str):
        sg_rules_ids = [
            rule['id'] for rule in sg['security_group_rules']]
        for sg_rule_id in sg_rules_ids:
            self._check_sg_rule_in_ovn_nb_db(sg_rule_id, expected_action)


@neutron.skip_if_missing_networking_extensions('stateful-security-group')
class StatelessSecurityGroupTest(BaseSecurityGroupTest):

    def test_default_security_group_is_stateful(self):
        """Test that default security group is always stateful.

        This test checks if default SG created for the project is stateful
        and if OVN's ACLs corresponding to the SG's rules have correct
        action which is "allow-related".

        Steps:
        1. Get default SG for the project (it's always created automatically),
        2. Check if ACLs corresponding to the rules from that SG have
           "action-related" action,
        3. Add new SG rule in the default SG,
        4. Check action of the ACL corresponding to the newly created SG rule.
        """

        default_sg = neutron.get_default_security_group(
            project_id=self.stack.project)
        self.assertTrue(default_sg['stateful'])
        self._check_sg_rules_in_ovn_nb_db(default_sg,
                                          neutron.STATEFUL_OVN_ACTION)
        new_rule = neutron.create_security_group_rule(
            default_sg['id'],
            port_range_min=1111,
            port_range_max=1111,
            ethertype="IPv4",
            protocol="tcp",
            description="test_default_security_group_is_stateful rule",
            direction="ingress"
        )
        self._check_sg_rule_in_ovn_nb_db(new_rule['id'],
                                         neutron.STATEFUL_OVN_ACTION)

    def test_new_security_group_is_stateful(self):
        """Test that newly created security group is stateful by default.

        This test checks if newly created SG is stateful by default
        and if OVN's ACLs corresponding to the SG's rules have correct
        action which is "allow-related".

        Steps:
        1. Create SG for the project,
        2. Check if ACLs corresponding to the rules from that SG have
           "action-related" action,
        3. Add new SG rule in the SG,
        4. Check action of the ACL corresponding to the newly created SG rule.
        """
        sg = neutron.create_security_group(
            name="test_new_security_group_is_statefull_SG",
        )
        self.assertTrue(sg['stateful'])
        self._check_sg_rules_in_ovn_nb_db(sg, neutron.STATEFUL_OVN_ACTION)
        new_rule = neutron.create_security_group_rule(
            sg['id'],
            port_range_min=1111,
            port_range_max=1111,
            ethertype="IPv4",
            protocol="tcp",
            description="test_new_security_group_is_statefull_SG rule",
            direction="ingress"
        )
        self._check_sg_rule_in_ovn_nb_db(new_rule['id'],
                                         neutron.STATEFUL_OVN_ACTION)
