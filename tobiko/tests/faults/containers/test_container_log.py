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

from oslo_log import log
import testtools

from tobiko.tests.faults.containers import container_ops


LOG = log.getLogger(__name__)


class LogFilesTest(testtools.TestCase):

    def test_neutron_logs_exist(self):
        groups = ['controller', 'compute', 'networker']
        neutron_nodes = container_ops.get_nodes_for_groups(groups)
        for node in neutron_nodes:
            containers = container_ops.get_node_neutron_containers(node)
            for container in containers:
                l_file = container_ops.get_container_logfile(node, container)
                if not l_file:
                    LOG.warning(f'No logfile has been found in {container} '
                                f'container of {node.name} node')
                    continue
                log_msg = container_ops.log_random_msg(node, container, l_file)
                l_node = f'/var/log/containers/neutron/{l_file.split("/")[-1]}'
                self.assertTrue(container_ops.find_msg_in_file(node,
                                                               l_node,
                                                               log_msg))
