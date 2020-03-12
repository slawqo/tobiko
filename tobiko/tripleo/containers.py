from __future__ import absolute_import

import os
import time
import functools

from oslo_log import log
import pandas
import podman as podmanlib
import docker as dockerlib

import tobiko
from tobiko import podman
from tobiko import docker
from tobiko.openstack import topology
from tobiko.tripleo import topology as tripleo_topology


LOG = log.getLogger(__name__)


def get_container_runtime_module():
    """check what container runtime is running
    and return a handle to it"""
    # TODO THIS LOCKS SSH CLIENT TO CONTROLLER
    ssh_client = topology.list_openstack_nodes(group='controller')[
        0].ssh_client
    if docker.is_docker_running(ssh_client=ssh_client):
        return docker
    else:
        return podman


container_runtime_module = get_container_runtime_module()


def get_container_runtime_name():
    return container_runtime_module.__name__.rsplit('.', 1)[1]


container_runtime_name = get_container_runtime_name()


def list_node_containers(client):
    """returns a list of containers and their run state"""

    if container_runtime_module == podman:
        return container_runtime_module.list_podman_containers(client=client)

    elif container_runtime_module == docker:
        return container_runtime_module.list_docker_containers(client=client)


def get_container_client(ssh_client=None):
    """returns a list of containers and their run state"""

    if container_runtime_module == podman:
        return container_runtime_module.get_podman_client(
            ssh_client=ssh_client).connect()

    elif container_runtime_module == docker:
        return container_runtime_module.get_docker_client(
            ssh_client=ssh_client).connect()


def list_containers_df(group=None):
    actual_containers_list = list_containers(group)
    return pandas.DataFrame(
        get_container_states_list(actual_containers_list),
        columns=['container_host', 'container_name', 'container_state'])


def list_containers(group=None):
    """get list of containers in running state
    from specified node group
    returns : a list of overcloud_node's running containers"""

    # moved here from topology
    # reason : Workaround for :
    # AttributeError: module 'tobiko.openstack.topology' has no
    # attribute 'container_runtime'

    containers_list = tobiko.Selection()
    if group:
        openstack_nodes = topology.list_openstack_nodes(group=group)
    else:
        openstack_controllers = topology.list_openstack_nodes(
            group='controller')
        openstack_computes = topology.list_openstack_nodes(group='compute')
        openstack_nodes = openstack_controllers + openstack_computes

    for node in openstack_nodes:
        ssh_client = node.ssh_client
        container_client = get_container_client(ssh_client)
        node_containers_list = list_node_containers(client=container_client)
        containers_list.extend(node_containers_list)
    return containers_list


expected_containers_file = '/home/stack/expected_containers_list_df.csv'


def save_containers_state_to_file(expected_containers_list,):
    expected_containers_list_df = pandas.DataFrame(
        get_container_states_list(expected_containers_list),
        columns=['container_host', 'container_name', 'container_state'])
    expected_containers_list_df.to_csv(
        expected_containers_file)
    return expected_containers_file


def assert_containers_running(group, expected_containers, full_name=True):

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
        for container in expected_containers:
            # get container attrs dataframe
            if full_name:
                container_attrs = containers_list_df.query(
                    'container_name == "{}"'.format(container))
            else:
                container_attrs = containers_list_df[
                    containers_list_df['container_name'].
                    str.contains(container)]
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
    # optional ovn containers checks
    assert_ovn_containers_running()


@functools.lru_cache()
def ovn_used_on_overcloud():
    return list_containers_df()['container_name'].\
            str.contains('ovn').any(axis=None)


def assert_ovn_containers_running():
    # specific OVN verifications
    if ovn_used_on_overcloud():
        # TODO: deployments with networker nodes are not supported
        ovn_controller_containers = ['ovn_controller',
                                     'ovn-dbs-bundle-{}-'.
                                     format(container_runtime_name)]
        ovn_compute_containers = ['ovn_metadata_agent',
                                  'ovn_controller']
        for group, group_containers in [('controller',
                                         ovn_controller_containers),
                                        ('compute',
                                         ovn_compute_containers)]:
            assert_containers_running(group, group_containers, full_name=False)
        LOG.info("Networking OVN containers verified")
    else:
        LOG.info("Networking OVN not configured")


def comparable_container_keys(container, include_container_objects=False):
    """returns the tuple : 'container_host','container_name',
    'container_state, container object if specified'
     """
    if container_runtime_module == podman and include_container_objects:
        return (tripleo_topology.ip_to_hostname(
            container._client._context.hostname),  # pylint: disable=W0212
                container.data['names'], container.data['status'],
                container)
    elif container_runtime_module == podman:
        return (tripleo_topology.ip_to_hostname(
            container._client._context.hostname),  # pylint: disable=W0212
                container.data['names'], container.data['status'])

    elif container_runtime_module == docker and include_container_objects:
        return (container.attrs['Config']['Hostname'],
                container.attrs['Name'].strip('/'),
                container.attrs['State']['Status'],
                container)
    elif container_runtime_module == docker:
        return (container.attrs['Config']['Hostname'],
                container.attrs['Name'].strip('/'),
                container.attrs['State']['Status'])


@functools.lru_cache()
def list_containers_objects_df():
    containers_list = list_containers()
    containers_objects_list_df = pandas.DataFrame(
        get_container_states_list(
            containers_list, include_container_objects=True),
        columns=['container_host', 'container_name',
                 'container_state', 'container_object'])
    return containers_objects_list_df


def get_overcloud_container(container_name=None, container_host=None):
    """gets an container object by name on specified host
    container"""
    con_obj_df = list_containers_objects_df()
    if container_host:
        contaniner_obj = con_obj_df.query(
            'container_name == "{container_name}"'
            ' and container_host == "{container_host}"'.
            format(container_host=container_host,
                   container_name=container_name))['container_object']
    else:
        contaniner_obj = con_obj_df.query(
            'container_name == "{container_name}"'.
            format(container_name=container_name))['container_object']
    if not contaniner_obj.empty:
        return contaniner_obj.values[0]
    else:
        tobiko.fail('container {} not found!'.format(container_name))


def action_on_container(action,
                        container_name=None, container_host=None):
    """take a container snd preform an action on it
    actions are as defined in : podman/libs/containers.py:14/164"""
    container = get_overcloud_container(
        container_name=container_name,
        container_host=container_host)
    # we get the specified action as function from podman lib
    if container_runtime_module == podman:
        container_function = getattr(
            podmanlib.libs.containers.Container, '{}'.format(action))
    else:
        container_function = getattr(
            dockerlib.models.containers.Container, '{}'.format(action))
    LOG.info('action_on_container: executing : {} on {}'.format(action,
                                                                container))
    return container_function(container)


def get_container_states_list(containers_list,
                              include_container_objects=False):
    container_states_list = tobiko.Selection()
    container_states_list.extend([comparable_container_keys(
        container, include_container_objects=include_container_objects) for
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


def assert_equal_containers_state(expected_containers_list=None,
                                  timeout=120, interval=2,
                                  recreate_expected=False):

    """compare all overcloud container states with using two lists:
    one is current , the other some past list
    first time this method runs it creates a file holding overcloud
    containers' states: /home/stack/expected_containers_list_df.csv'
    second time it creates a current containers states list and
    compares them, they must be identical"""

    # if we have a file or an explicit variable use that , otherwise  create
    # and return
    if recreate_expected or (not expected_containers_list and
                             not os.path.exists(expected_containers_file)):
        save_containers_state_to_file(list_containers())
        return

    elif expected_containers_list:
        expected_containers_list_df = pandas.DataFrame(
            get_container_states_list(expected_containers_list),
            columns=['container_host', 'container_name', 'container_state'])

    elif os.path.exists(expected_containers_file):
        expected_containers_list_df = pandas.read_csv(
            expected_containers_file)

    failures = []
    start = time.time()
    error_info = 'Output explanation: left_only is the original state, ' \
                 'right_only is the new state'

    while time.time() - start < timeout:

        failures = []
        actual_containers_list_df = list_containers_df()

        LOG.info('expected_containers_list_df: {} '.format(
            expected_containers_list_df.to_string(index=False)))
        LOG.info('actual_containers_list_df: {} '.format(
            actual_containers_list_df.to_string(index=False)))

        # execute a `dataframe` diff between the expected and actual containers
        expected_containers_state_changed = \
            dataframe_difference(expected_containers_list_df,
                                 actual_containers_list_df)
        # check for changed state containerstopology
        if not expected_containers_state_changed.empty:
            failures.append('expected containers changed state ! : '
                            '\n\n{}\n{}'.format(
                             expected_containers_state_changed.
                             to_string(index=False), error_info))
            LOG.info('container states mismatched:\n{}\n'.format(failures))
            time.sleep(interval)
        else:
            LOG.info("assert_equal_containers_state :"
                     " OK, all containers are on the same state")
            return
    if failures:
        tobiko.fail('container states mismatched:\n{!s}', '\n'.join(
            failures))