from __future__ import absolute_import

import random
from oslo_log import log

import testtools
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.tests.faults.ha import cloud_disruptions
from tobiko.tripleo import pacemaker
from tobiko.tripleo import processes
from tobiko.tripleo import containers
from tobiko.tripleo import nova
from tobiko.tripleo import neutron
from tobiko.tripleo import undercloud
from tobiko.openstack import stacks
import tobiko


LOG = log.getLogger(__name__)


def overcloud_health_checks(passive_checks_only=False):
    # this method will be changed in future commit
    check_pacemaker_resources_health()
    check_overcloud_processes_health()
    nova.check_nova_services_health()
    neutron.check_neutron_agents_health()
    if not passive_checks_only:
        # create a uniq stack
        check_vm_create()
    else:
        # verify VM status is updated after reboot
        nova.wait_for_all_instances_status('SHUTOFF')
    nova.start_all_instances()
    containers.list_node_containers.cache_clear()
    containers.assert_all_tripleo_containers_running()
    containers.assert_equal_containers_state()


# check vm create with ssh and ping checks
def check_vm_create(stack_name='stack{}'.format(random.randint(0, 1000000))):
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


def check_overcloud_node_responsive(node):
    """wait until we get response for hostname command"""
    hostname_check = sh.execute("hostname", ssh_client=node.ssh_client,
                                expect_exit_status=None).stdout
    LOG.info('{} is up '.format(hostname_check))


# check cluster failed statuses
def check_pacemaker_resources_health():
    return pacemaker.PacemakerResourcesStatus().all_healthy


def check_overcloud_processes_health():
    return processes.OvercloudProcessesStatus(
            ).basic_overcloud_processes_running


@undercloud.skip_if_missing_undercloud
class RebootTripleoNodesTest(testtools.TestCase):

    """ HA Tests: run health check -> disruptive action -> health check
    disruptive_action: a function that runs some
    disruptive scenarion on a overcloud"""
    def test_overcloud_health_check(self):
        overcloud_health_checks()

    def test_reboot_controllers_recovery(self):
        overcloud_health_checks()
        cloud_disruptions.disrupt_all_controller_nodes()
        overcloud_health_checks()

    def test_hard_reboot_controllers_recovery(self):
        overcloud_health_checks()
        cloud_disruptions.reset_all_controller_nodes()
        overcloud_health_checks()

    def test_sequentially_hard_reboot_controllers_recovery(self):
        overcloud_health_checks()
        cloud_disruptions.reset_all_controller_nodes_sequentially()
        overcloud_health_checks()

    def test_reboot_computes_recovery(self):
        overcloud_health_checks()
        cloud_disruptions.reset_all_compute_nodes(hard_reset=True)
        overcloud_health_checks(passive_checks_only=True)

    def test_reboot_controller_main_vip(self):
        overcloud_health_checks()
        cloud_disruptions.reset_controller_main_vip()
        overcloud_health_checks()

    def test_reboot_controller_non_main_vip(self):
        overcloud_health_checks()
        cloud_disruptions.reset_controllers_non_main_vip()
        overcloud_health_checks()

    def test_network_disruptor_main_vip(self):
        overcloud_health_checks()
        cloud_disruptions.network_disrupt_controller_main_vip()
        overcloud_health_checks()
        cloud_disruptions.network_undisrupt_controller_main_vip()

    def test_network_disruptor_non_main_vip(self):
        overcloud_health_checks()
        cloud_disruptions.network_disrupt_controllers_non_main_vip()
        overcloud_health_checks()
        cloud_disruptions.network_undisrupt_controllers_non_main_vip()

    def test_reset_ovndb_master_resource(self):
        overcloud_health_checks()
        cloud_disruptions.reset_ovndb_master_resource()
        overcloud_health_checks()

    def test_reset_ovndb_master_container(self):
        overcloud_health_checks()
        cloud_disruptions.reset_ovndb_master_container()
        overcloud_health_checks()
# [..]
# more tests to follow
# run health checks
# faults stop rabbitmq service on one controller
# run health checks again
