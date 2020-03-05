from __future__ import absolute_import

import time

from oslo_log import log
import pandas

import tobiko
from tobiko import podman
from tobiko import docker
from tobiko.openstack import topology


LOG = log.getLogger(__name__)


def container_runtime():
    """check what container runtime is running
    and return a handle to it"""
    # TODO THIS LOCKS SSH CLIENT TO CONTROLLER
    ssh_client = topology.list_openstack_nodes(group='controller')[
        0].ssh_client
    if docker.is_docker_running(ssh_client=ssh_client):
        return docker
    else:
        return podman


container_runtime_type = container_runtime()


def list_node_containers(client):
    """returns a list of containers and their run state"""

    if container_runtime_type == podman:
        return container_runtime_type.list_podman_containers(client=client)

    elif container_runtime_type == docker:
        return container_runtime_type.list_docker_containers(client=client)


def get_container_client(ssh_client=None):
    """returns a list of containers and their run state"""

    if container_runtime_type == podman:
        return container_runtime_type.get_podman_client(
            ssh_client=ssh_client).connect()

    elif container_runtime_type == docker:
        return container_runtime_type.get_docker_client(
            ssh_client=ssh_client).connect()


def list_containers(group=None):
    """get list of containers in running state
    from specified node group
    returns : a list of overcloud_node's running containers"""

    # moved here from topology
    # reason : Workaround for :
    # AttributeError: module 'tobiko.openstack.topology' has no
    # attribute 'container_runtime'

    containers_list = tobiko.Selection()
    openstack_nodes = topology.list_openstack_nodes(group=group)

    for node in openstack_nodes:
        ssh_client = node.ssh_client
        container_client = get_container_client(ssh_client)
        node_containers_list = list_node_containers(client=container_client)
        containers_list.extend(node_containers_list)
    return containers_list


def assert_containers_running(group, excpected_containers):

    """assert that all containers specified in the list are running
    on the specified openstack group(controller or compute etc..)"""

    failures = []

    openstack_nodes = topology.list_openstack_nodes(group=group)
    for node in openstack_nodes:
        container_client = get_container_client(node.ssh_client)
        node_containers = list_node_containers(client=container_client)
        containers_list_df = pandas.DataFrame(
            get_container_states_list(node_containers),
            columns=['container_host', 'container_name', 'container_state'])
        # check that the containers are present
        LOG.info('node: {} containers list : {}'.format(
            node.name, containers_list_df.to_string(index=False)))
        for container in excpected_containers:
            # get container attrs dataframe
            container_attrs = containers_list_df.query(
                'container_name == "{}"'.format(container))
            # check if the container exists
            LOG.info('checking container: {}'.format(container))
            if container_attrs.empty:
                failures.append(
                    'expected container {} not found on node {} ! : \n\n'.
                    format(container, node.name))
            # if container exists, check it is running
            else:
                container_state = \
                    container_attrs.container_state.values.item()
                if not container_state == 'running':
                    failures.append(
                        'expected container {} is not running on node {} , '
                        'its state is {}! : \n\n'.format(container,
                                                         node.name,
                                                         container_state))

    if failures:
        tobiko.fail('container states mismatched:\n{!s}', '\n'.join(failures))
    else:
        LOG.info('All tripleo common containers are in running state! ')


def assert_all_tripleo_containers_running():
    """check that all common tripleo containers are running
    param: group controller or compute , check containers
    sets in computes or controllers"""

    common_controller_tripleo_containers = ['cinder_api', 'cinder_api_cron',
                                            'cinder_scheduler', 'clustercheck',
                                            'glance_api', 'heat_api',
                                            'heat_api_cfn',
                                            'heat_api_cron', 'heat_engine',
                                            'horizon', 'iscsid', 'keystone',
                                            'logrotate_crond', 'memcached',
                                            'neutron_api', 'nova_api',
                                            'nova_api_cron', 'nova_conductor',
                                            'nova_metadata', 'nova_scheduler',
                                            'nova_vnc_proxy',
                                            'swift_account_auditor',
                                            'swift_account_reaper',
                                            'swift_account_replicator',
                                            'swift_account_server',
                                            'swift_container_auditor',
                                            'swift_container_replicator',
                                            'swift_container_server',
                                            'swift_container_updater',
                                            'swift_object_auditor',
                                            'swift_object_expirer',
                                            'swift_object_replicator',
                                            'swift_object_server',
                                            'swift_object_updater',
                                            'swift_proxy', 'swift_rsync']

    common_compute_tripleo_containers = ['iscsid', 'logrotate_crond',
                                         'nova_compute', 'nova_libvirt',
                                         'nova_migration_target',
                                         'nova_virtlogd']

    for group, group_containers in [('controller',
                                     common_controller_tripleo_containers),
                                    ('compute',
                                     common_compute_tripleo_containers)]:
        assert_containers_running(group, group_containers)
    # TODO: need to address OSP-version specific containers here.


def comparable_container_keys(container):
    """returns the tuple : 'container_host','container_name',
    'container_state'
     """
    if container_runtime_type == podman:
        return (container._client._context.hostname,  # pylint: disable=W0212
                container.data['names'], container.data['status'])

    elif container_runtime_type == docker:
        return (container.attrs['Config']['Hostname'],
                container.attrs['Name'].strip('/'),
                container.attrs['State']['Status'])


def get_container_states_list(containers_list):
    container_states_list = tobiko.Selection()
    container_states_list.extend([comparable_container_keys(container) for
                                  container in containers_list])
    return container_states_list


def dataframe_difference(df1, df2, which=None):
    """Find rows which are different between two DataFrames."""
    comparison_df = df1.merge(df2,
                              indicator='same_state',
                              how='outer')
    if which is None:
        diff_df = comparison_df[comparison_df['same_state'] != 'both']
    else:
        diff_df = comparison_df[comparison_df['same_state'] == which]
    return diff_df


def assert_equal_containers_state(expected_containers_list,
                                  actual_containers_list, timeout=120,
                                  interval=2):

    """compare container with states from two lists"""

    failures = []
    start = time.time()

    expected_containers_list_df = pandas.DataFrame(
        get_container_states_list(expected_containers_list),
        columns=['container_host', 'container_name', 'container_state'])

    while time.time() - start < timeout:

        failures = []
        actual_containers_list_df = pandas.DataFrame(
            get_container_states_list(actual_containers_list),
            columns=['container_host', 'container_name', 'container_state'])

        LOG.info('expected_containers_list_df: {} '.format(
            expected_containers_list_df.to_string(index=False)))
        LOG.info('actual_containers_list_df: {} '.format(
            actual_containers_list_df.to_string(index=False)))

        # execute a dataframe diff between the excpected and actual containers
        expected_containers_state_changed = \
            dataframe_difference(expected_containers_list_df,
                                 actual_containers_list_df)
        # check for changed state containers
        if not expected_containers_state_changed.empty:
            failures.append('expected containers changed state ! : '
                            '\n\n{}'.format(expected_containers_state_changed.
                                            to_string(index=False)))
            LOG.info('container states mismatched:\n{}\n'.format(failures))
            time.sleep(interval)
            LOG.info('Retrying , timeout at: {}'
                     .format(timeout-(time.time() - start)))
            actual_containers_list = list_containers(group='compute')
        else:
            LOG.info("assert_equal_containers_state :"
                     " OK, all containers are on the same state")
            return
    if failures:
        tobiko.fail('container states mismatched:\n{!s}', '\n'.join(failures))
