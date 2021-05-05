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

from oslo_log import log
import testtools

import tobiko
from tobiko.openstack import stacks
from tobiko.openstack import topology
from tobiko.shell import iperf
from tobiko.tripleo import containers
from tobiko.tripleo import overcloud


LOG = log.getLogger(__name__)


class QoSBasicTest(testtools.TestCase):
    """Tests QoS basic functionality"""

    #: Resources stack with QoS Policy and QoS Rules and Advanced server
    stack = tobiko.required_setup_fixture(stacks.UbuntuQosServerStackFixture)

    def setUp(self):
        """Skip these tests if OVN is configured and OSP version is lower than
        16.1
        """
        super(QoSBasicTest, self).setUp()
        if (overcloud.has_overcloud() and
                topology.verify_osp_version('16.0', lower=True) and
                containers.ovn_used_on_overcloud()):
            self.skipTest("QoS not supported in this setup")

    def test_network_qos_policy_id(self):
        '''Verify QoS Policy attached to the network corresponds with the QoS
        Policy previously created'''
        self.assertEqual(self.stack.network_stack.qos_stack.qos_policy_id,
                         self.stack.network_stack.qos_policy_id)

    def test_server_qos_policy_id(self):
        self.assertIsNone(self.stack.port_details['qos_policy_id'])

    def test_qos_bw_limit(self):
        '''Verify BW limit using the iperf tool
        '''
        iperf.assert_bw_limit(ssh_client=None,  # localhost will act as client
                              ssh_server=self.stack.peer_ssh_client)
