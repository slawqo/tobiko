from __future__ import absolute_import

import testtools

from tobiko.openstack import neutron
from tobiko.openstack import tests
from tobiko.tests.faults.ha import cloud_disruptions
from tobiko.tripleo import pacemaker
from tobiko.tripleo import processes
from tobiko.tripleo import containers
from tobiko.tripleo import nova
from tobiko.tripleo import undercloud
from tobiko.tripleo import validations


def overcloud_health_checks(passive_checks_only=False,
                            skip_mac_table_size_test=True):
    # this method will be changed in future commit
    check_pacemaker_resources_health()
    check_overcloud_processes_health()
    nova.check_nova_services_health()
    tests.test_neutron_agents_are_alive()
    if not passive_checks_only:
        # create a uniq stack
        check_vm_create()
        nova.start_all_instances()
        nova.check_computes_vms_running_via_virsh()
    containers.list_node_containers.cache_clear()
    containers.assert_all_tripleo_containers_running()
    containers.assert_equal_containers_state()
    containers.run_container_config_validations()
    tests.test_ovn_dbs_validations()
    # skip_mac_table_size_test has to be removed when BZ1695122 is resolved
    # we need it for the moment because this validation should not be performed
    # after any overcloud node is rebooted
    if not skip_mac_table_size_test:
        tests.test_ovs_bridges_mac_table_size()
    validations.run_post_deployment_validations()


# check vm create with ssh and ping checks
def check_vm_create():
    tests.test_server_creation()


# check cluster failed statuses
def check_pacemaker_resources_health():
    return pacemaker.PacemakerResourcesStatus().all_healthy


def check_overcloud_processes_health():
    procs = processes.OvercloudProcessesStatus()
    return (procs.basic_overcloud_processes_running and
            procs.ovn_overcloud_processes_validations)


@undercloud.skip_if_missing_undercloud
class DisruptTripleoNodesTest(testtools.TestCase):

    """ HA Tests: run health check -> disruptive action -> health check
    disruptive_action: a function that runs some
    disruptive scenarion on a overcloud"""
    def test_0vercloud_health_check(self):
        overcloud_health_checks(skip_mac_table_size_test=False)

    def test_hard_reboot_controllers_recovery(self):
        overcloud_health_checks()
        cloud_disruptions.reset_all_controller_nodes()
        overcloud_health_checks()

    def test_reboot_computes_recovery(self):
        overcloud_health_checks()
        cloud_disruptions.reset_all_compute_nodes(hard_reset=True)
        # verify VM status is updated after reboot
        nova.wait_for_all_instances_status('SHUTOFF')
        # start all VM instance
        # otherwise sidecar containers will not run after computes reboot
        nova.start_all_instances()
        overcloud_health_checks(passive_checks_only=True)

    def test_reboot_controller_main_vip(self):
        overcloud_health_checks()
        cloud_disruptions.reset_controller_main_vip()
        overcloud_health_checks()

    def test_reboot_controller_non_main_vip(self):
        overcloud_health_checks()
        cloud_disruptions.reset_controllers_non_main_vip()
        overcloud_health_checks()

    @pacemaker.skip_if_fencing_not_deployed
    def test_network_disruptor_main_vip(self):
        overcloud_health_checks()
        cloud_disruptions.network_disrupt_controller_main_vip()
        overcloud_health_checks()
        cloud_disruptions.network_undisrupt_controller_main_vip()

    # @pacemaker.skip_if_fencing_not_deployed
    # def test_network_disruptor_non_main_vip(self):
    #     overcloud_health_checks()
    #     cloud_disruptions.network_disrupt_controllers_non_main_vip()
    #     overcloud_health_checks()
    #     cloud_disruptions.network_undisrupt_controllers_non_main_vip()

    @neutron.skip_unless_is_ovn()
    def test_reset_ovndb_pcs_master_resource(self):
        overcloud_health_checks()
        cloud_disruptions.reset_ovndb_pcs_master_resource()
        overcloud_health_checks()

    @neutron.skip_unless_is_ovn()
    def test_reset_ovndb_pcs_resource(self):
        overcloud_health_checks()
        cloud_disruptions.reset_ovndb_pcs_resource()
        overcloud_health_checks()

    @neutron.skip_unless_is_ovn()
    def test_reset_ovndb_master_container(self):
        overcloud_health_checks()
        cloud_disruptions.reset_ovndb_master_container()
        overcloud_health_checks()

    def test_kill_rabbitmq_service_one_controller(self):
        overcloud_health_checks()
        cloud_disruptions.kill_rabbitmq_service()
        overcloud_health_checks()

    def test_kill_all_galera_services(self):
        overcloud_health_checks()
        cloud_disruptions.kill_all_galera_services()
        overcloud_health_checks()

# [..]
# more tests to follow
# run health checks
# faults stop rabbitmq service on one controller
# run health checks again
