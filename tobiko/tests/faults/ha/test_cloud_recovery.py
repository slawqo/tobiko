from __future__ import absolute_import

import random

import testtools
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.tests.faults.ha import cloud_disruptions
from tobiko.tripleo import pacemaker
from tobiko.tripleo import processes
from tobiko.tripleo import containers
from tobiko.tripleo import nova
from tobiko.openstack import stacks
import tobiko


def overcloud_health_checks(passive_checks_only=False):
    # this method will be changed in future commit
    # check_pacemaker_resources_health()
    # check_overcloud_processes_health()
    # nova.check_nova_services_health()
    # neutron.check_neutron_agents_health()
    if not passive_checks_only:
        # create a uniq stack
        check_vm_create(stack_name='stack{}'.format(random.randint(0, 10000)))
    nova.start_all_instances()
    # containers.assert_all_tripleo_containers_running()
    containers.assert_equal_containers_state()


# check vm create with ssh and ping checks
def check_vm_create(stack_name):
    """stack_name: unique stack name ,
    so that each time a new vm is created"""
    # create a vm
    stack = stacks.CirrosServerStackFixture(
        stack_name=stack_name)
    tobiko.reset_fixture(stack)
    stack.wait_for_create_complete()
    # Test SSH connectivity to floating IP address
    sh.get_hostname(ssh_client=stack.ssh_client)

    # Test ICMP connectivity to floating IP address
    ping.ping_until_received(
        stack.floating_ip_address).assert_replied()


# check cluster failed statuses
def check_pacemaker_resources_health():
    return pacemaker.PacemakerResourcesStatus().all_healthy


def check_overcloud_processes_health():
    return processes.OvercloudProcessesStatus(
            ).basic_overcloud_processes_running


class RebootNodesTest(testtools.TestCase):

    """ HA Tests: run health check -> disruptive action -> health check
    disruptive_action: a function that runs some
    disruptive scenarion on a overcloud"""
    def test_overcloud_health_check(self):
        overcloud_health_checks()

    def test_reboot_controllers_recovery(self):
        overcloud_health_checks()
        cloud_disruptions.reset_all_controller_nodes()
        overcloud_health_checks()

    def test_reboot_computes_recovery(self):
        overcloud_health_checks()
        cloud_disruptions.reset_all_compute_nodes(hard_reset=True)
        overcloud_health_checks(passive_checks_only=True)


# [..]
# more tests to follow
# run health checks
# faults stop rabbitmq service on one controller
# run health checks again
