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

import re

from oslo_log import log
import testtools

from tobiko.openstack import topology
from tobiko.shell import sh


LOG = log.getLogger(__name__)


class ConfigurationFilesTest(testtools.TestCase):

    def get_filtered_node_containers(self, node, containers_regex):
        """Search all containers are matched with containers_regex list
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
        # The following code causes test to take 4 times more time
        # podman = node.podman_client.setup_client()
        # for container in podman.containers.list():
        #     if any(re.fullmatch(reg, container) for reg in containers_regex):
        #         filtered_containers.append(container.names)
        return filtered_containers

    def verify_config_files(self, node, containers, file_list, service):
        """Verify that files on the node are equal to the file in container

        It calculates MD5 sum of the configuration file in the changed
        directory if it exists there or in original directory otherwise.
        It also follows any links if necessary.
        """
        original_dir = f'/var/lib/config-data/{service}'
        changed_dir = f'/var/lib/config-data/puppet-generated/{service}'
        verified = True
        for fname in file_list:
            flink = sh.execute(
                    f'sudo readlink {changed_dir}{fname} || '
                    f'sudo readlink {original_dir}{fname}',
                    ssh_client=node.ssh_client,
                    expect_exit_status=None).stdout.strip() or fname
            md5_output = sh.execute(
                    f'sudo md5sum {changed_dir}{fname} || '
                    f'sudo md5sum {changed_dir}{flink} || '
                    f'sudo md5sum {original_dir}{fname} || '
                    f'sudo md5sum {original_dir}{flink}',
                    ssh_client=node.ssh_client,
                    expect_exit_status=None).stdout.strip().split(' ')
            if md5_output:
                md5 = md5_output[0]
                LOG.debug(f'{md5_output[-1]} on {node.name} has {md5} MD5')
            else:
                md5 = ''
                verified = False
                LOG.error(f'{node.name}: {fname} doesn\'t exist in '
                          f'{original_dir} or {changed_dir}')
            for container in containers:
                container_md5 = sh.execute(
                        f'sudo podman exec -it -u root {container} md5sum '
                        f'-z {fname} | awk \'{{print $1}}\'',
                        ssh_client=node.ssh_client,
                        expect_exit_status=None).stdout.strip()
                LOG.debug(f'{fname} in {container} container '
                          f'has {container_md5} md5 hash')
                if container_md5 != md5:
                    LOG.error(f'incorrect md5 for {fname}. '
                              f'{node.name}: {md5}, {container} container: '
                              f'{container_md5}')
                    verified = False
        return verified

    def get_neutron_nodes(self):
        nodes = []
        supported_groups = ['controller', 'compute', 'networker']
        for node in topology.list_openstack_nodes():
            for group in node.groups:
                if group in supported_groups:
                    nodes.append(node)
        return(nodes)

    def get_node_neutron_containers(self, node):
        neutron_containers = [
                'neutron_((ovs|metadata|l3)_agent|dhcp|api)',
                'ovn_(controller|metadata_agent)',
                r'ovn-dbs-bundle-(podman|docker)-\d*']
        return self.get_filtered_node_containers(node, neutron_containers)

    def get_node_neutron_config_files(self, node):
        """Return the list of configuration files according to kolla JSONs

        Kolla has the container execution commands in the matched JSON files.
        Need to get all the '--config-file <file_name>' parameters from those
        JSON files.
        It is possible that the container is executed with the set of commands
        are written in a separate script instead of a single command so need
        to follow those scripts to get configuration files from there too.
        """
        neutron_cmds = sh.execute(
                'sudo jq \'.command\' /var/lib/kolla/config_files/neutron* '
                '/var/lib/kolla/config_files/ovn*',
                ssh_client=node.ssh_client,
                expect_exit_status=None).stdout.strip().split('\n')
        LOG.debug(f'{node.name} run containers with commands {neutron_cmds}')
        conf_ignorelist = ['/usr/share/neutron/neutron-dist.conf']
        scripts_to_check = {'"/neutron_ovs_agent_launcher.sh"':
                            '/var/lib/container-config-scripts/'
                            'neutron_ovs_agent_launcher.sh'}
        neutron_config_files = set()
        for cmd in neutron_cmds:
            if cmd in scripts_to_check.keys():
                LOG.debug(f'{cmd} is recognized as script to search '
                          'for config files in')
                cmd = sh.execute(
                        f'sudo cat {scripts_to_check[cmd]}',
                        ssh_client=node.ssh_client,
                        expect_exit_status=None).stdout.strip()
            cmd = cmd.strip('"')
            conf_files = re.findall('--config-file [^ ]*', cmd)
            for conf_file in conf_files:
                conf_file = conf_file.split(' ')[1]
                if conf_file in conf_ignorelist:
                    LOG.debug(f'{conf_file} is in ignore list')
                    continue
                neutron_config_files.add(conf_file)
        LOG.debug(f'There are {neutron_config_files} on {node.name}')
        return neutron_config_files

    def test_neutron_config_files(self):
        neutron_nodes = self.get_neutron_nodes()
        for node in neutron_nodes:
            neutron_containers = self.get_node_neutron_containers(node)
            neutron_config_files = self.get_node_neutron_config_files(node)
            self.assertTrue(
                    self.verify_config_files(node,
                                             neutron_containers,
                                             neutron_config_files,
                                             'neutron'))
