from __future__ import absolute_import

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


def get_pcs_resources_table():
    """
    get pcs status from a controller and parse it
    to have it's resources states in check
       returns :
       rabbitmq-bundle-0    (ocf::heartbeat:rabbitmq-cluster):      Started con
       troller-0
       rabbitmq-bundle-1    (ocf::heartbeat:rabbitmq-cluster):      Started con
       troller-1
       rabbitmq-bundle-2    (ocf::heartbeat:rabbitmq-cluster):      Started con
       troller-2
       galera-bundle-0      (ocf::heartbeat:galera):        Master controller-0
       galera-bundle-1      (ocf::heartbeat:galera):        Master controller-1
       galera-bundle-2      (ocf::heartbeat:galera):        Master controller-2
       redis-bundle-0       (ocf::heartbeat:redis): Master controller-0
       redis-bundle-1       (ocf::heartbeat:redis): Slave controller-1
       redis-bundle-2       (ocf::heartbeat:redis): Slave controller-2
     ip-192.168.24.6        (ocf::heartbeat:IPaddr2):       Started controller-
     0
     ip-10.0.0.101  (ocf::heartbeat:IPaddr2):       Started controller-1
     ip-172.17.1.12 (ocf::heartbeat:IPaddr2):       Started controller-2
     ip-172.17.1.22 (ocf::heartbeat:IPaddr2):       Started controller-0
     ip-172.17.3.22 (ocf::heartbeat:IPaddr2):       Started controller-1
     ip-172.17.4.30 (ocf::heartbeat:IPaddr2):       Started controller-2
       haproxy-bundle-docker-0      (ocf::heartbeat:docker):        Started con
       troller-0
       haproxy-bundle-docker-1      (ocf::heartbeat:docker):        Started con
       troller-1
       haproxy-bundle-docker-2      (ocf::heartbeat:docker):        Started con
       troller-2
       openstack-cinder-volume-docker-0     (ocf::heartbeat:docker):        Sta
       rted controller-0

    :return: dataframe of pcs resources stats table
    """
    # TODO make more robust(done, need other methods to be too)
    # TODO make table.columns retry without exception

    nodes = topology.list_openstack_nodes(group='controller')
    controller_node = nodes[0].name
    ssh_client = overcloud.overcloud_ssh_client(controller_node)

    # prevent pcs table read failure while pacemaker is starting
    while True:
        try:
            output = sh.execute("sudo pcs status | grep ocf",
                                ssh_client=ssh_client,
                                expect_exit_status=None).stdout
            stream = six.StringIO(output)
            table = pandas.read_csv(stream, delim_whitespace=True, header=None)

            table.columns = ['resource', 'resource_type', 'resource_state',
                             'overcloud_node']
        except ValueError:
            pass
        else:
            break
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
        if self.container_runtime() == 'podman':
            nodes_num = self.resource_count("(ocf::heartbeat:redis):")
            if nodes_num > 0:
                return True
            else:
                master_num = self.resource_count_in_state(
                    "(ocf::heartbeat:redis):", "Master")
                slave_num = self.resource_count_in_state(
                    "(ocf::heartbeat:redis):", "Slave")
                if (master_num == 1) and (slave_num == nodes_num - master_num):
                    LOG.info(
                        "pcs status check: resource ovn is in healthy state")
                    return True
                else:
                    LOG.info(
                        "pcs status check: resource ovn is in not in "
                        "healthy state")
                    return False
        else:
            return True

    @property
    def all_healthy(self):
        """
        check if each resource is in healthy order
        and return a global healthy status
        :return: Bool
        """
        for _ in range(360):

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
                self.pcs_df = get_pcs_resources_table()
        # exhausted all retries
        return False


def get_overcloud_nodes_running_pcs_resource(resource=None,
                                             resource_type=None,
                                             resource_state=None):
    """
    Check what nodes are running the specified resource/type/state
    resource/type/state: exact str of a process name as seen in pcs status
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
