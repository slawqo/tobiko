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

import typing

import testtools
from oslo_log import log

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import octavia
from tobiko.openstack import stacks
from tobiko.shell.ssh import SSHClientFixture
from tobiko.openstack import topology
from tobiko.shell import sh
from tobiko.openstack.topology import OpenStackTopologyNode


LOG = log.getLogger(__name__)


@keystone.skip_if_missing_service(name='octavia')
class OctaviaServicesFaultTest(testtools.TestCase):
    """Octavia services fault test.

    Create a load balancer with 2 members that run a server application,
    Create a client that is connected to the load balancer VIP port,
    Generate network traffic from the client to the load balancer while
    stopping some of the Octavia's services - if the container runtime
    environment is podman.

    Each service will be running as a single instance.
    E.g. only one WORKER_SERVICE will run in all controllers, the same for
    API_SERVICE etc.

    Then we test that traffic which is being sent from the client to the LB
    is received as expected.
    """
    loadbalancer_stack = tobiko.required_setup_fixture(
        stacks.AmphoraIPv4LoadBalancerStack)

    listener_stack = tobiko.required_setup_fixture(
        stacks.HttpRoundRobinAmphoraIpv4Listener)

    list_octavia_active_units = ('systemctl list-units ' +
                                 '--state=active tripleo_octavia_*')

    controllers = None

    def setUp(self):
        # pylint: disable=no-member
        super(OctaviaServicesFaultTest, self).setUp()

        # Skip the test if there are no 3 available controllers -> e.g. Tripleo
        self.controllers = topology.list_openstack_nodes(group='controller')

        if 3 != len(self.controllers):
            skip_reason = "The number of controllers should be 3 for this test"
            self.skipTest(skip_reason)

        # Wait for Octavia objects to be active
        LOG.info('Waiting for member '
                 f'{self.listener_stack.server_stack.stack_name} and '
                 f'for member '
                 f'{self.listener_stack.other_server_stack.stack_name} '
                 f'to be created...')
        self.listener_stack.wait_for_active_members()

        self.loadbalancer_stack.wait_for_octavia_service()

        self.listener_stack.wait_for_members_to_be_reachable()

        # Sending initial traffic before we stop octavia services
        octavia.check_members_balanced(
            pool_id=self.listener_stack.pool_id,
            ip_address=self.loadbalancer_stack.floating_ip_address,
            lb_algorithm=self.listener_stack.lb_algorithm,
            protocol=self.listener_stack.lb_protocol,
            port=self.listener_stack.lb_port)

    def test_services_fault(self):
        # excluded_services are the services which will be stopped
        # on each controller
        excluded_services = {
            "controller-0": [octavia.API_SERVICE],
            "controller-1": [octavia.WORKER_SERVICE],
            "controller-2": [octavia.HM_SERVICE, octavia.HOUSEKEEPING_SERVICE]
        }

        try:
            for controller in self.controllers:
                self._make_sure_octavia_services_are_active(controller)

                self._stop_octavia_main_services(
                    controller, excluded_services[controller.name])

        finally:
            self._start_octavia_main_services(self.controllers)

    def _make_sure_octavia_services_are_active(
            self, controller: OpenStackTopologyNode):

        actual_services = self._list_octavia_services(controller.ssh_client)
        for service in octavia.OCTAVIA_SERVICES:
            err_msg = (f'{service} is inactive on {controller.name}. '
                       + 'It should have been active')
            self.assertTrue(service in actual_services, err_msg)
        LOG.debug("All Octavia services are running")

    def _list_octavia_services(self, ssh_client: SSHClientFixture) -> str:
        """Return the octavia services status.

        This method returns the OUTPUT of the command we run to enlist the
        services.
        """

        # Return "list Octavia services" command's output
        octavia_services = sh.execute(self.list_octavia_active_units,
                                      ssh_client=ssh_client, sudo=True).stdout
        octavia_services_output = f'Octavia units are:\n{octavia_services}'
        LOG.debug(octavia_services_output)
        return octavia_services

    def _stop_octavia_main_services(self, controller: OpenStackTopologyNode,
                                    excluded_services: typing.List[str]):

        """Stops the provided octavia services.

        This method stops the provided octavia services, except for the ones
        which are in excluded_services.
        After it runs the "stop command" (e.g. `systemctl stop`),
        it makes sure that the Octavia's stopped services do not appear on
        the running Octavia services.

        It then sends traffic to validate the Octavia's functionality
        """

        # Preparing the services to stop
        services_to_stop = octavia.OCTAVIA_SERVICES

        if excluded_services:
            services_to_stop = [service for service in services_to_stop if (
                    service not in excluded_services)]

        # Stopping the Octavia services
        for service in services_to_stop:
            command = f"systemctl stop {service}"

            sh.execute(command, ssh_client=controller.ssh_client, sudo=True)

            log_msg = f"Stopping {service} on {controller.name}"
            LOG.info(log_msg)

        # Making sure the Octavia services were stopped
        octavia_active_units = self._list_octavia_services(
            controller.ssh_client)

        for service in services_to_stop:
            err_msg = f'{service} was not stopped on {controller.name}'
            self.assertTrue(service not in octavia_active_units, err_msg)

        self.loadbalancer_stack.wait_for_octavia_service()

        octavia.check_members_balanced(
            pool_id=self.listener_stack.pool_id,
            ip_address=self.loadbalancer_stack.floating_ip_address,
            lb_algorithm=self.listener_stack.lb_algorithm,
            protocol=self.listener_stack.lb_protocol,
            port=self.listener_stack.lb_port)

    def _start_octavia_main_services(
            self, controllers: typing.List[OpenStackTopologyNode] = None):

        """Starts the provided octavia services.

        This method starts the provided octavia services.
        After it runs the "start command" (e.g. `systemctl start`), it makes
        sure that the Octavia services appear on the active Octavia units.

        It then sends traffic to validate the Octavia's functionality
        """

        controllers = controllers or topology.list_openstack_nodes(
            group='controller')
        for controller in controllers:

            # Starting the Octavia services
            for service in octavia.OCTAVIA_SERVICES:
                sh.execute(f"systemctl start {service}",
                           ssh_client=controller.ssh_client, sudo=True)

            # Making sure the Octavia services were started
            self._make_sure_octavia_services_are_active(controller)

        octavia.check_members_balanced(
            pool_id=self.listener_stack.pool_id,
            ip_address=self.loadbalancer_stack.floating_ip_address,
            lb_algorithm=self.listener_stack.lb_algorithm,
            protocol=self.listener_stack.lb_protocol,
            port=self.listener_stack.lb_port)
