from __future__ import absolute_import

import random

import testtools
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.tests.faults.ha import cloud_disruptions
from tobiko.tripleo import pacemaker
from tobiko.tripleo import processes
from tobiko.tripleo import containers
from tobiko.tripleo import neutron
from tobiko.openstack import stacks
import tobiko


def nodes_health_check():
    # this method will be changed in future commit
    check_pacemaker_resources_health()
    check_overcloud_processes_health()
    neutron.check_neutron_agents_health()
    # create a uniq stack
    check_vm_create(stack_name='stack{}'.format(random.randint(0, 10000)))

    # TODO:
    # Test existing created serverstest_controller_containers
    # ServerStackResourcesTest().test_server_create()
    # Add specific container checks


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

    def test_reboot_controllers_recovery(self):
        nodes_health_check()
        cloud_disruptions.reset_all_controller_nodes()
        nodes_health_check()

    def test_reboot_computes_recovery(self):
        nodes_health_check()
        computes_containers_dict_before = \
            containers.list_containers(group='compute')
        cloud_disruptions.reset_all_compute_nodes(hard_reset=True)
        nodes_health_check()
        computes_containers_dict_after = \
            containers.list_containers(group='compute')
        containers.assert_equal_containers_state(
            computes_containers_dict_before, computes_containers_dict_after)

# [..]
# more tests to folow
# run health checks
# os faults stop rabbitmq service on one controller
# run health checks again
