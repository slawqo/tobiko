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
from tobiko import tripleo
from tobiko.openstack import keystone
from tobiko.openstack import octavia
from tobiko.openstack import stacks
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


@tripleo.skip_if_missing_overcloud
@keystone.skip_if_missing_service(name='octavia')
class OctaviaOVNProviderTrafficTest(testtools.TestCase):
    """Octavia OVN provider traffic test.

    Create an OVN provider load balancer with 2 members that run a server
    application,
    Create a client that is connected to the load balancer VIP port via FIP,
    Generate network traffic from the client to the load balanacer via ssh.
    """
    loadbalancer_stack = tobiko.required_setup_fixture(
        stacks.OctaviaOvnProviderLoadbalancerStackFixture)

    listener_stack = tobiko.required_setup_fixture(
        stacks.OctaviaOvnProviderListenerStackFixture)

    pool_stack = tobiko.required_setup_fixture(
        stacks.OctaviaOvnProviderPoolStackFixture)

    member1_stack = tobiko.required_setup_fixture(
        stacks.OctaviaOvnProviderMemberServerStackFixture)

    member2_stack = tobiko.required_setup_fixture(
        stacks.OctaviaOvnProviderOtherMemberServerStackFixture)

    def setUp(self):
        # pylint: disable=no-member
        super(OctaviaOVNProviderTrafficTest, self).setUp()

        # Wait for Octavia objects to be active
        LOG.info(f'Waiting for {self.member1_stack.stack_name} and '
                 f'{self.member2_stack.stack_name} to be created...')
        self.pool_stack.wait_for_active_members()

        octavia.wait_for_octavia_service(
            loadbalancer_id=self.loadbalancer_stack.loadbalancer_id)

    def test_ovn_provider_traffic(self):
        LOG.info('Trying to ssh each member and print "test #<num>"')
        for i in range(len(octavia.list_members(self.pool_stack.pool_id))):
            command = f'echo test {i}'

            my_ssh_client = ssh.ssh_client(
                username='cirros',
                host=self.loadbalancer_stack.floating_ip_address,
                password='cubswin:)')

            out = sh.execute(command, ssh_client=my_ssh_client).stdout
            LOG.info(out)

            if out.endswith('\n'):
                out = out[:-1]
            expected_out = f'test {i}'
            self.assertEqual(expected=expected_out, observed=out)
