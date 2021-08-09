from __future__ import absolute_import

import typing

from oslo_log import log
import testtools

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack import tests
from tobiko.tests.faults.ha import cloud_disruptions
from tobiko.tripleo import pacemaker
from tobiko.tripleo import processes
from tobiko.tripleo import containers
from tobiko.tripleo import nova
from tobiko.tripleo import undercloud


LOG = log.getLogger(__name__)


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


class OvercloudHealthCheck(tobiko.SharedFixture):

    skips: typing.FrozenSet[str] = frozenset()

    @classmethod
    def run_before(cls, **params):
        cls.run(after=False, **params)

    @classmethod
    def run_after(cls, **params):
        cls.run(after=True, **params)

    @classmethod
    def run(cls, after: bool, **params):
        fixture = tobiko.get_fixture(cls)
        params.setdefault('passive_checks_only', False)
        params.setdefault('skip_mac_table_size_test', True)
        skips = frozenset(k for k, v in params.items() if v)
        if after or skips < fixture.skips:
            # Force re-check
            tobiko.cleanup_fixture(fixture)
        else:
            LOG.info("Will skip Overcloud health checks if already "
                     f"executed: {params}")
        fixture.skips = skips
        tobiko.setup_fixture(fixture)

    def setup_fixture(self):
        # run validations
        params = {name: True
                  for name in self.skips}
        LOG.info(f"Start executing Overcloud health checks: {params}.")
        overcloud_health_checks(**params)
        LOG.info(f"Overcloud health checks successfully executed: {params}.")

    def cleanup_fixture(self):
        self.skips = frozenset()


@undercloud.skip_if_missing_undercloud
class DisruptTripleoNodesTest(testtools.TestCase):
    """ HA Tests: run health check -> disruptive action -> health check
    disruptive_action: a function that runs some
    disruptive scenario on a overcloud"""

    def test_0vercloud_health_check(self):
        OvercloudHealthCheck.run_before(skip_mac_table_size_test=False)

    def test_hard_reboot_controllers_recovery(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.reset_all_controller_nodes()
        OvercloudHealthCheck.run_after()

    def test_soft_reboot_computes_recovery(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.reset_all_compute_nodes(hard_reset=False)
        # verify VM status is updated after reboot
        nova.wait_for_all_instances_status('SHUTOFF')
        # start all VM instance
        # otherwise sidecar containers will not run after computes reboot
        nova.start_all_instances()
        OvercloudHealthCheck.run_after(passive_checks_only=True)

    # TODO(eolivare): the following test is skipped due to rhbz#1890895
    # def test_hard_reboot_computes_recovery(self):
    #     OvercloudHealthCheck.run_before()
    #     cloud_disruptions.reset_all_compute_nodes(hard_reset=True)
    #     # verify VM status is updated after reboot
    #     nova.wait_for_all_instances_status('SHUTOFF')
    #     # start all VM instance
    #     # otherwise sidecar containers will not run after computes reboot
    #     nova.start_all_instances()
    #     OvercloudHealthCheck.run_after(passive_checks_only=True)

    def test_z99_reboot_controller_main_vip(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.reset_controller_main_vip()
        OvercloudHealthCheck.run_after()

    def test_z99_reboot_controller_non_main_vip(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.reset_controllers_non_main_vip()
        OvercloudHealthCheck.run_after()

    def test_z99_crash_controller_main_vip(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.crash_controller_main_vip()
        OvercloudHealthCheck.run_after()

    def test_z99_crash_controller_non_main_vip(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.crash_controllers_non_main_vip()
        OvercloudHealthCheck.run_after()

    @pacemaker.skip_if_fencing_not_deployed
    def test_network_disruptor_main_vip(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.network_disrupt_controller_main_vip()
        OvercloudHealthCheck.run_after()
        cloud_disruptions.network_undisrupt_controller_main_vip()

    # @pacemaker.skip_if_fencing_not_deployed
    # def test_network_disruptor_non_main_vip(self):
    #     OvercloudHealthCheck.run_before()
    #     cloud_disruptions.network_disrupt_controllers_non_main_vip()
    #     OvercloudHealthCheck.run_after()
    #     cloud_disruptions.network_undisrupt_controllers_non_main_vip()

    @neutron.skip_unless_is_ovn()
    def test_reset_ovndb_pcs_master_resource(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.reset_ovndb_pcs_master_resource()
        OvercloudHealthCheck.run_after()

    @neutron.skip_unless_is_ovn()
    def test_reset_ovndb_pcs_resource(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.reset_ovndb_pcs_resource()
        OvercloudHealthCheck.run_after()

    @neutron.skip_unless_is_ovn()
    def test_reset_ovndb_master_container(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.reset_ovndb_master_container()
        OvercloudHealthCheck.run_after()

    def test_kill_rabbitmq_service_one_controller(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.kill_rabbitmq_service()
        OvercloudHealthCheck.run_after()

    def test_kill_all_galera_services(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.kill_all_galera_services()
        OvercloudHealthCheck.run_after()

    def test_remove_all_grastate_galera(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.remove_all_grastate_galera()
        OvercloudHealthCheck.run_after()

    def test_remove_one_grastate_galera(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.remove_one_grastate_galera()
        OvercloudHealthCheck.run_after()

    def test_request_galera_sst(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.request_galera_sst()
        OvercloudHealthCheck.run_after()

    def test_controllers_shutdown(self):
        OvercloudHealthCheck.run_before()
        cloud_disruptions.test_controllers_shutdown()
        OvercloudHealthCheck.run_after()

# [..]
# more tests to follow
# run health checks
# faults stop rabbitmq service on one controller
# run health checks again
