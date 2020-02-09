from __future__ import absolute_import

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

    ssh_client = topology.list_openstack_nodes(group='controller')[
        0].ssh_client
    if docker.is_docker_running(ssh_client=ssh_client):
        return docker
    else:
        return podman


container_runtime_type = container_runtime()


def list_node_containers(client=None):
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


def comparable_container_keys(container):
    """returns the tuple : 'container_host','container_name',
    'container_state'
     """
    if container_runtime_type == podman:
        return (container._client._context.hostname,  # pylint: disable=W0212
                container.data['names'], container.data['status'])

    elif container_runtime_type == docker:
        return (container.attrs['Config']['Hostname'],
                container.attrs['State']['Status'], container.attrs['Name'])


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
                                  actual_containers_list):

    """compare container with states from two lists"""

    failures = []
    expected_containers_list_df = pandas.DataFrame(
        get_container_states_list(expected_containers_list),
        columns=['container_host', 'container_name', 'container_state'])
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
        failures.append('expected containers changed state ! : \n\n{}'.format(
            expected_containers_state_changed.to_string(index=False)))

    if failures:
        tobiko.fail('container states mismatched:\n{!s}', '\n'.join(failures))
    else:
        LOG.info("assert_equal_containers_state :"
                 " OK, all containers are on the same state")
