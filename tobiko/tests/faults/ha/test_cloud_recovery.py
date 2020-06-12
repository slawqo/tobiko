from __future__ import absolute_import

import testtools
from tobiko.tests.faults.ha import cloud_disruptions
from tobiko.tripleo import pacemaker
from tobiko.tripleo import processes
from tobiko.tripleo import containers
from tobiko.tripleo import nova
from tobiko.tripleo import neutron
from tobiko.tripleo import undercloud
from tobiko.tripleo import validations


def overcloud_health_checks(passive_checks_only=False):
    # this method will be changed in future commit
    check_pacemaker_resources_health()
    check_overcloud_processes_health()
    nova.check_nova_services_health()
    neutron.check_neutron_agents_health()
    if not passive_checks_only:
        # create a uniq stack
        check_vm_create()
        nova.start_all_instances()
    containers.list_node_containers.cache_clear()
    containers.assert_all_tripleo_containers_running()
    containers.assert_equal_containers_state()
    validations.run_post_deployment_validations()


# check vm create with ssh and ping checks
def check_vm_create():
    nova.random_vm_create()


# check cluster failed statuses
def check_pacemaker_resources_health():
    return pacemaker.PacemakerResourcesStatus().all_healthy


def check_overcloud_processes_health():
    return processes.OvercloudProcessesStatus(
            ).basic_overcloud_processes_running


@undercloud.skip_if_missing_undercloud
class DisruptTripleoNodesTest(testtools.TestCase):

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

    def test_reboot_computes_recovery(self):
        overcloud_health_checks()
        cloud_disruptions.reset_all_compute_nodes(hard_reset=True)
        # verify VM status is updated after reboot
        nova.wait_for_all_instances_status('SHUTOFF')
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

    @pacemaker.skip_if_instanceha_not_delpoyed
    def test_instanceha_evacuation_hard_reset(self):
        overcloud_health_checks()
        cloud_disruptions.check_iha_evacuation_hard_reset()

    @pacemaker.skip_if_instanceha_not_delpoyed
    def test_instanceha_evacuation_network_disruption(self):
        overcloud_health_checks()
        cloud_disruptions.check_iha_evacuation_network_disruption()

    def test_instanceha_evacuation_hard_reset_shutfoff_inatance(self):
        overcloud_health_checks()
        cloud_disruptions.check_iha_evacuation_hard_reset_shutfoff_inatance()

    def test_check_instanceha_evacuation_evac_image_vm(self):
        overcloud_health_checks()
        cloud_disruptions.check_iha_evacuation_evac_image_vm()


# [..]
# more tests to follow
# run health checks
# faults stop rabbitmq service on one controller
# run health checks again
