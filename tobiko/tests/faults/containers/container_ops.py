# Copyright (c) 2020 Red Hat
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import absolute_import

import random
import re

from oslo_log import log

from tobiko import fail
from tobiko.openstack import topology
from tobiko.shell import sh


LOG = log.getLogger(__name__)


def get_filtered_node_containers(node, containers_regex):
    """Search all containers are matched with containers_regex list

    :param node: Node to search containers on
    :type node: class: tobiko.openstack.topology.OpenStackTopologyNode
    :param containers_regex: List of regex that can be matched to containers
    :type containers_regex: list of strings
    :return: List of contatiner names
    :rtype: list of strings
    """
    filtered_containers = []
    all_node_containers = sh.execute(
            'sudo podman ps --format "{{.Names}}"',
            ssh_client=node.ssh_client,
            expect_exit_status=None
            ).stdout.strip().split('\n')
    for container in all_node_containers:
        container = container.strip('"')
        if any(re.fullmatch(reg, container) for reg in containers_regex):
            filtered_containers.append(container)
    return filtered_containers


def get_nodes_for_groups(groups):
    """Search for all nodes that are matched with the specified groups

    :param groups: List of groups nodes can belong to
    :type groups: list
    :return: List of nodes that belong to the specified groups
    :rtype: list of tobiko.openstack.topology.OpenStackTopologyNode
    """
    nodes = []
    for node in topology.list_openstack_nodes():
        for group in node.groups:
            if group in groups:
                nodes.append(node)
    return(nodes)


def get_config_files(node, kolla_jsons, conf_ignorelist, scripts_to_check):
    """Return the list of configuration files according to kolla JSONs

    Kolla has the container execution commands in the matched JSON files.
    Need to get all the '--config-file <file_name>' parameters from those
    JSON files.
    It is possible that the container is executed with the set of commands
    are written in a separate script instead of a single command so need
    to follow those scripts to get configuration files from there too.

    :param node: Node to search configuration files on
    :type node: class: tobiko.openstack.topology.OpenStackTopologyNode
    :param kolla_jsons: Path to kolla json files to get commands from
    :type kolla_jsons: list
    :param conf_ignorelist: Configuration files to ignore
    :type conf_ignorelist: list
    :param scripts_to_check: Sripts to look for configuration files in if those
        scripts will be found in kolla json files. Dictionary contains script
        path on the container as the key and the path on the overcloud node
        as the value.
    :type scripts_to_check: dict
    :return: List of config files paths within containers
    :rtype: list
    """
    cmds = sh.execute(
            f'sudo jq \'.command\' {" ".join(kolla_jsons)}',
            ssh_client=node.ssh_client,
            expect_exit_status=None).stdout.strip().split('\n')
    LOG.debug(f'{node.name} run containers with commands {cmds}')
    config_files = set()
    for cmd in cmds:
        if cmd in scripts_to_check.keys():
            LOG.debug(f'{cmd} is recognized as script to search '
                      'for config files in')
            cmd = sh.execute(
                    f'sudo cat {scripts_to_check[cmd]}',
                    ssh_client=node.ssh_client,
                    expect_exit_status=None).stdout.strip()
        cmd = cmd.strip('"')
        temp_conf_files = re.findall('--config-file [^ \n]*', cmd)
        for conf_file in temp_conf_files:
            conf_file = conf_file.split(' ')[1]
            if conf_file in conf_ignorelist:
                LOG.debug(f'{conf_file} is in ignore list')
                continue
            config_files.add(conf_file)
    LOG.debug(f'There are {config_files} on {node.name}')
    return config_files


def get_node_neutron_containers(node):
    """Return list of all neutron containers are available on the node

    :param node: Node to search containers on
    :type node: class: tobiko.openstack.topology.OpenStackTopologyNode
    :return: List of neutron containers names
    :rtype: list of strings
    """
    neutron_containers = [
            'neutron_((ovs|metadata|l3)_agent|dhcp|api)',
            'ovn_(controller|metadata_agent)',
            r'ovn-dbs-bundle-(podman|docker)-\d*']
    return get_filtered_node_containers(node, neutron_containers)


def get_node_neutron_config_files(node):
    """Return all relevant neutron config files

    :param node: Overcloud node to search log files on
    :type node: class: tobiko.openstack.topology.OpenStackTopologyNode
    :return: List of config files paths within neutron containers
    :rtype: list of strings
    """
    kolla_jsons = ['/var/lib/kolla/config_files/neutron*',
                   '/var/lib/kolla/config_files/ovn*']
    conf_ignorelist = ['/usr/share/neutron/neutron-dist.conf']
    scripts_to_check = {'"/neutron_ovs_agent_launcher.sh"':
                        '/var/lib/container-config-scripts/'
                        'neutron_ovs_agent_launcher.sh'}
    config_files = get_config_files(node,
                                    kolla_jsons,
                                    conf_ignorelist,
                                    scripts_to_check)
    return config_files


def get_container_logfile(node, container):
    """ Return the logfile of the process that is executed on the container

    :param node: Node the container is running on
    :type node: class: tobiko.openstack.topology.OpenStackTopologyNode
    :param container: Name of the container
    :type container: string
    :return: Path to the logfiles on the container
    :rtype: string
    """
    cmd = sh.execute(
            f'sudo podman exec -it -u root {container} cat /run_command',
            ssh_client=node.ssh_client,
            expect_exit_status=None).stdout.strip()
    if ' ' not in cmd:  # probably script as no space in the command
        cmd = sh.execute(
                f'sudo podman exec -it -u root {container} cat {cmd}',
                ssh_client=node.ssh_client,
                expect_exit_status=None).stdout.strip()
    LOG.debug(f'The following command is executed in {container} container '
              f'on {node.name} node:\n{cmd}')
    log_file = re.findall('--log-file=[^ \n]*', cmd)
    if log_file:
        log_file = log_file[0].split('=')[1]
    return log_file


def log_random_msg(node, container, logfile):
    """Print random message to the container log file

    :param node: Node the container is running on
    :type node: class: tobiko.openstack.topology.OpenStackTopologyNode
    :param container: Name of the container
    :type container: string
    :param logfile: Path to the logfile on the container
    :type logfile: string
    :return: Message that has been printed to container log file
    :rtype: string
    """
    symbols = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    random_msg = ''.join(random.choice(symbols) for i in range(30))
    LOG.debug(f'Trying to print {random_msg} string to {logfile} log file '
              f'in {container} container on {node.name} node')
    cmd = f"sh -c 'echo {random_msg} >> {logfile}'"
    error = sh.execute(f'sudo podman exec -it -u root {container} {cmd}',
                       ssh_client=node.ssh_client,
                       expect_exit_status=None).stderr
    if error:
        fail(f'Cannot edit {logfile} in {container} on {node.name} '
             f'got the following error:\n{error}')
    return random_msg


def find_msg_in_file(node, logfile, message):
    """Search for the message in the logfile

    :param node: Node the container is running on
    :type node: class: tobiko.openstack.topology.OpenStackTopologyNode
    :param logfile: Path of the logfile
    :type logfile: string
    :param message: Message to search for
    :type message: string
    :return: True if message exists in file or False otherwise
    :rtype: bool
    """
    LOG.debug(f'Searching for {message} in {logfile} on {node.name}')
    result = sh.execute(f'sudo grep -h {message} {logfile}{{,.1}}',
                        ssh_client=node.ssh_client,
                        expect_exit_status=None)
    if result.stderr:
        fail(f'Failed reading {logfile} on {node.name}:\n{result.stderr}')
    elif result.stdout.strip() == message:
        return True
    else:
        return False
