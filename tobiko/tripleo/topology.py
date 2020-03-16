# Copyright 2019 Red Hat
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

from tobiko.openstack import topology
from tobiko.tripleo import overcloud
from tobiko.tripleo import undercloud


LOG = log.getLogger(__name__)


class TripleoTopology(topology.OpenStackTopology):

    agent_to_service_name_mappings = {
        'neutron-dhcp-agent': 'tripleo_neutron_dhcp',
    }

    def discover_nodes(self):
        self.discover_undercloud_nodes()
        self.discover_overcloud_nodes()

    def discover_undercloud_nodes(self):
        if undercloud.has_undercloud():
            config = undercloud.undercloud_host_config()
            ssh_client = undercloud.undercloud_ssh_client()
            self.add_node(address=config.hostname,
                          group='undercloud',
                          ssh_client=ssh_client)

    def discover_overcloud_nodes(self):
        if overcloud.has_overcloud():
            for server in overcloud.list_overcloud_nodes():
                config = overcloud.overcloud_host_config(server.name)
                ssh_client = overcloud.overcloud_ssh_client(server.name)
                node = self.add_node(address=config.hostname,
                                     group='overcloud',
                                     ssh_client=ssh_client)

                group = node.name.split('-', 1)[0]
                if group == node.name:
                    LOG.warning("Unable to get node group name node name: %r",
                                node.name)
                else:
                    self.add_node(hostname=node.name, group=group)
        else:
            super(TripleoTopology, self).discover_nodes()


def setup_tripleo_topology():
    if undercloud.has_undercloud() or overcloud.has_overcloud():
        topology.set_default_openstack_topology_class(
            'tobiko.tripleo.topology.TripleoTopology')


def get_ip_to_nodes_dict(openstack_nodes=None):
    if not openstack_nodes:
        openstack_nodes = topology.list_openstack_nodes(group='overcloud')
    ip_to_nodes_dict = {str(node.public_ip): node.name for node in
                        openstack_nodes}
    return ip_to_nodes_dict


def str_is_not_ip(check_str):
    letters = re.compile('[A-Za-z]')
    return bool(letters.match(check_str))


def ip_to_hostname(oc_ip):
    return get_ip_to_nodes_dict()[oc_ip]
