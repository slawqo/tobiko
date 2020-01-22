from __future__ import absolute_import

import testtools

from tobiko.tests.faults.ha import cloud_disruptions
from tobiko.tripleo import pacemaker
from tobiko.tripleo import processes


def nodes_health_check():
    # this method will be changed in future commit
    check_pacemaker_resources_health()
    check_overcloud_processes_health()
    # TODO:
    # Test existing created servers
    # ServerStackResourcesTest().test_server_create()


# check cluster failed statuses
def check_pacemaker_resources_health():
    return pacemaker.PacemakerResourcesStatus().all_healthy


def check_overcloud_processes_health():
    return processes.OvercloudProcessesStatus(
            ).basic_overcloud_processes_running

# TODO:
# class ServerStackResourcesTest(testtools.TestCase):
#
#     """Tests connectivity via floating IPs"""
#
#     #: Resources stack with floating IP and Nova server
#     # TODO move down :
#     # stack = tobiko.required_setup_fixture(stacks.CirrosServerStackFixture)
#     # stack = tobiko.setup(my_instace) #tobiko.setup(my_instace)
#
#     # TODO new instances of the class , give a uniq stack name
#     # TODO : create a new CirrosServerStackFixture ?
#     #  CirrosServerStackNameFixture(stack_name='my-unique-id')
#     # tobiko.setup(my_instace) -> tobiko.cleanup(my_instance)
#     def test_create_vm(self):
#         """Test SSH connectivity to floating IP address"""
#         stack = tobiko.setup(my_instace)  # tobiko.setup(my_instace)
#         tobiko.cleanup(my_instance)
#         # TODO : add check if old vm is there
#         hostname = sh.get_hostname(ssh_client=self.stack.ssh_client)
#         self.assertEqual(self.stack.server_name.lower(), hostname)


class RebootNodesTest(testtools.TestCase):

    """ HA Tests: run health check -> disruptive action -> health check
    disruptive_action: a function that runs some
    disruptive scenarion on a overcloud"""

    def test_reboot_controllers_recovery(self):
        nodes_health_check()
        cloud_disruptions.reset_all_controller_nodes_sequentially()
        nodes_health_check()


# [..]
# more tests to folow
# run health checks
# os faults stop rabbitmq service on one controller
# run health checks again
