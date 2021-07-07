from __future__ import absolute_import

import time

from oslo_log import log
import pandas
import six

import tobiko
from tobiko.tripleo import overcloud
from tobiko.shell import sh
from tobiko.openstack import topology


LOG = log.getLogger(__name__)


class PcsResourceException(tobiko.TobikoException):
    message = "pcs cluster is not in a healthy state"


def get_random_controller_ssh_client():
    """get a random controler's ssh client """
    nodes = topology.list_openstack_nodes(group='controller')
    controller_node = nodes[0]
    return controller_node.ssh_client


def get_pcs_resources_table(timeout=720, interval=2):
    """
    get pcs status from a controller and parse it
    to have it's resources states in check
       returns :
       rabbitmq-bundle-0    (ocf::heartbeat:rabbitmq-cluster):      Started con
       troller-0
     ip-10.0.0.101  (ocf::heartbeat:IPaddr2):       Started controller-1
       openstack-cinder-volume-docker-0     (ocf::heartbeat:docker):        Sta
       rted controller-0

    :return: dataframe of pcs resources stats table
    """
    failures = []
    start = time.time()

    ssh_client = get_random_controller_ssh_client()

    # prevent pcs table read failure while pacemaker is starting
    while time.time() - start < timeout:
        failures = []
        try:
            output = sh.execute("sudo pcs status resources |grep ocf",
                                ssh_client=ssh_client,
                                expect_exit_status=None).stdout
            # remove the first column when it only includes '*' characters
            output = output.replace('*', '').strip()
            stream = six.StringIO(output)
            table = pandas.read_csv(stream, delim_whitespace=True, header=None)
            table.columns = ['resource', 'resource_type', 'resource_state',
                             'overcloud_node']
        except ValueError:
            pcs_status_raw = sh.execute("sudo pcs status ",
                                        ssh_client=ssh_client,
                                        expect_exit_status=None).stdout
            failures.append(f'pcs status table import failed : '
                            f'pcs status stdout:\n {pcs_status_raw}')
            LOG.info('Retrying , timeout at: {}'
                     .format(timeout-(time.time() - start)))
            time.sleep(interval)
        else:
            break
    # exhausted all retries
    if failures:
        tobiko.fail(
            'pcs status table import error\n{!s}', '\n'.join(failures))

    LOG.debug("Got pcs status :\n%s", table)
    return table


class PacemakerResourcesStatus(object):
    """
    class to handle pcs resources checks
    """
    def __init__(self):
        self.pcs_df = get_pcs_resources_table()

    def container_runtime(self):
        if not self.pcs_df[(self.pcs_df['resource_type'] ==
                            "(ocf::heartbeat:docker):")].empty:
            return 'docker'
        if not self.pcs_df[(self.pcs_df['resource_type'] ==
                            "(ocf::heartbeat:podman):")].empty:
            return 'podman'

    def resource_count(self, resource_type):
        return self.pcs_df[(self.pcs_df['resource_type'] == resource_type)][
            'resource_state'].count()

    def resource_count_in_state(self, resource_type, resource_state):
        return self.pcs_df[(self.pcs_df['resource_type'] ==
                            resource_type) & (self.pcs_df['resource_state'] ==
                                              resource_state)][
            'resource_state'].count()

    def rabbitmq_resource_healthy(self):
        nodes_num = self.resource_count("(ocf::heartbeat:rabbitmq-cluster):")
        started_num = self.resource_count_in_state(
            "(ocf::heartbeat:rabbitmq-cluster):", "Started")
        if nodes_num == started_num:
            LOG.info("pcs status check: resource rabbitmq is in healthy state")
            return True
        else:
            LOG.info("pcs status check: resource rabbitmq not in healthy "
                     "state")
            return False

    def galera_resource_healthy(self):
        nodes_num = self.resource_count("(ocf::heartbeat:galera):")
        master_num = self.resource_count_in_state("(ocf::heartbeat:galera):",
                                                  "Master")
        if nodes_num == master_num:
            LOG.info("pcs status check: resource galera is in healthy state")
            return True
        else:
            LOG.info("pcs status check: resource galera not in healthy state")
            return False

    def redis_resource_healthy(self):
        nodes_num = self.resource_count("(ocf::heartbeat:redis):")
        master_num = self.resource_count_in_state(
            "(ocf::heartbeat:redis):", "Master")
        slave_num = self.resource_count_in_state(
            "(ocf::heartbeat:redis):", "Slave")
        if (master_num == 1) and (slave_num == nodes_num - master_num):
            LOG.info("pcs status check: resource redis is in healthy state")
            return True
        else:
            LOG.info("pcs status check: resource redis not in healthy state")
            return False

    def vips_resource_healthy(self):
        nodes_num = self.resource_count("(ocf::heartbeat:IPaddr2):")
        started_num = self.resource_count_in_state(
            "(ocf::heartbeat:IPaddr2):", "Started")
        if nodes_num == started_num:
            LOG.info("pcs status check: resources vips are in healthy state")
            return True
        else:
            LOG.info(
                "pcs status check: resources vips are not in healthy state")
            return False

    def ha_proxy_cinder_healthy(self):

        nodes_num = self.resource_count("(ocf::heartbeat:{}):".format(
            self.container_runtime()))
        started_num = self.resource_count_in_state(
            "(ocf::heartbeat:{}):".format(self.container_runtime()), "Started")
        if nodes_num == started_num:
            LOG.info("pcs status check: resources ha_proxy and"
                     " cinder are in healthy state")
            return True
        else:
            LOG.info(
                "pcs status check: resources ha_proxy and cinder are not in "
                "healthy state")
            return False

    def ovn_resource_healthy(self):
        if self.pcs_df.query(
                'resource_type == "(ocf::ovn:ovndb-servers):"').empty:
            LOG.info('pcs status check: ovn is not deployed, skipping ovn '
                     'resource check')
            return True
        nodes_num = self.resource_count("(ocf::ovn:ovndb-servers):")
        master_num = self.resource_count_in_state(
            "(ocf::ovn:ovndb-servers):", "Master")
        slave_num = self.resource_count_in_state(
            "(ocf::ovn:ovndb-servers):", "Slave")
        if (master_num == 1) and (slave_num == nodes_num - master_num):
            LOG.info(
                "pcs status check: resource ovn is in healthy state")
            return True
        else:
            LOG.info(
                "pcs status check: resource ovn is in not in "
                "healthy state")
            return False

    @property
    def all_healthy(self):
        """
        check if each resource is in healthy order
        and return a global healthy status
        :return: Bool
        """
        for attempt_number in range(360):

            try:

                if all([
                   self.rabbitmq_resource_healthy(),
                   self.galera_resource_healthy(),
                   self.redis_resource_healthy(),
                   self.vips_resource_healthy(),
                   self.ha_proxy_cinder_healthy(),
                   self.ovn_resource_healthy()
                   ]):
                    LOG.info("pcs status checks: all resources are"
                             " in healthy state")
                    return True
                else:

                    LOG.info("pcs status check: not all resources are "
                             "in healthy "
                             "state")
                    raise PcsResourceException()
            except PcsResourceException:
                # reread pcs status
                LOG.info('Retrying pacemaker resource checks attempt '
                         '{} of 360'.format(attempt_number))
                time.sleep(1)
                self.pcs_df = get_pcs_resources_table()
        # exhausted all retries
        tobiko.fail('pcs cluster is not in a healthy state')


def get_overcloud_nodes_running_pcs_resource(resource=None,
                                             resource_type=None,
                                             resource_state=None):
    """
    Check what nodes are running the specified resource/type/state
    resource/type/state: exact str of a resource name as seen in pcs status
    :return: list of overcloud nodes
    """
    pcs_df = get_pcs_resources_table()
    if resource:
        pcs_df_query_resource = pcs_df.query('resource=="{}"'.format(
                                        resource))
        return pcs_df_query_resource['overcloud_node'].unique().tolist()

    if resource_type and resource_state:
        pcs_df_query_resource_type_state = pcs_df.query(
            'resource_type=="{}" and resource_state=="{}"'.format(
                resource_type, resource_state))
        return pcs_df_query_resource_type_state[
            'overcloud_node'].unique().tolist()

    if resource_type and not resource_state:
        pcs_df_query_resource_type = pcs_df.query(
            'resource_type=="{}"'.format(resource_type))
        return pcs_df_query_resource_type['overcloud_node'].unique().tolist()


def get_resource_master_node(resource_type=None):
    get_overcloud_nodes_running_pcs_resource(
        resource_type=resource_type, resource_state='Master')


def get_ovn_db_master_node():
    return get_overcloud_nodes_running_pcs_resource(
        resource_type='(ocf::ovn:ovndb-servers):', resource_state='Master')


def get_overcloud_resource(resource_type=None,
                           resource_state=None):
    """
    Check what nodes are running the specified resource/type/state
    resource/type/state: exact str of a resource name as seen in pcs status
    :return: list of overcloud nodes
    """
    pcs_df = get_pcs_resources_table()

    if resource_type and resource_state:
        pcs_df_query_resource_type_state = pcs_df.query(
            'resource_type=="{}" and resource_state=="{}"'.format(
                resource_type, resource_state))
        return pcs_df_query_resource_type_state[
            'resource'].unique().tolist()

    if resource_type and not resource_state:
        pcs_df_query_resource_type = pcs_df.query(
            'resource_type=="{}"'.format(resource_type))
        return pcs_df_query_resource_type['resource'].unique().tolist()


def instanceha_deployed():
    """check IHA deployment
    checks for existence of the nova-evacuate resource"""
    if overcloud.has_overcloud():
        return get_overcloud_nodes_running_pcs_resource(
            resource='nova-evacuate')
    else:
        return False


skip_if_instanceha_not_delpoyed = tobiko.skip_unless(
    'instanceha not delpoyed', instanceha_deployed)


def fencing_deployed():
    """check fencing deployment
    checks for existence of the stonith-fence type resources"""
    ssh_client = get_random_controller_ssh_client()
    fencing_output = sh.execute("sudo pcs status |grep "
                                "'stonith:fence_ipmilan'",
                                ssh_client=ssh_client,
                                expect_exit_status=None)

    if fencing_output.exit_status == 0:
        return True
    else:
        return False


skip_if_fencing_not_deployed = tobiko.skip_unless(
    'fencing not delpoyed', fencing_deployed)
