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
import typing  # noqa

from oslo_log import log

from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import topology
from tobiko.shell import files
from tobiko.shell import sh
from tobiko.tripleo import _overcloud
from tobiko.tripleo import _undercloud


LOG = log.getLogger(__name__)


class TripleoTopology(topology.OpenStackTopology):

    agent_to_service_name_mappings = {
        neutron.DHCP_AGENT: 'tripleo_neutron_dhcp',
        neutron.L3_AGENT:  'tripleo_neutron_l3_agent',
        neutron.OPENVSWITCH_AGENT: 'tripleo_neutron_ovs_agent',
        neutron.METADATA_AGENT: 'tripleo_neutron_metadata_agent',
        neutron.OVN_METADATA_AGENT: 'tripleo_ovn_metadata_agent',
        neutron.NEUTRON_OVN_METADATA_AGENT: 'tripleo_ovn_metadata_agent',
        neutron.OVN_CONTROLLER: 'tripleo_ovn_controller'
    }

    agent_to_container_name_mappings = {
        neutron.DHCP_AGENT: 'neutron_dhcp',
        neutron.L3_AGENT:  'neutron_l3_agent',
        neutron.OPENVSWITCH_AGENT: 'neutron_ovs_agent',
        neutron.METADATA_AGENT: 'neutron_metadata_agent',
        neutron.OVN_METADATA_AGENT: 'ovn_metadata_agent',
        neutron.NEUTRON_OVN_METADATA_AGENT: 'ovn_metadata_agent',
        neutron.OVN_CONTROLLER: 'ovn_controller'
    }

    has_containers = True

    # TODO: add more known subgrups here
    known_subgroups: typing.List[str] = ['controller', 'compute']

    # In TripleO we need to parse log files directly
    file_digger_class = files.LogFileDigger

    # This is dict which handles mapping of the log file and systemd_unit (if
    # needed) for the OpenStack services
    # Format of this dict is like below:
    # service_name: (log_filename, systemd_unit_name)
    log_names_mappings = {
        neutron.SERVER: '/var/log/containers/neutron/server.log*',
    }

    def create_node(self, name, ssh_client, **kwargs):
        return TripleoTopologyNode(topology=self,
                                   name=name,
                                   ssh_client=ssh_client,
                                   **kwargs)

    def discover_nodes(self):
        self.discover_ssh_proxy_jump_node()
        self.discover_undercloud_nodes()
        self.discover_overcloud_nodes()

    def discover_undercloud_nodes(self):
        if _undercloud.has_undercloud():
            config = _undercloud.undercloud_host_config()
            ssh_client = _undercloud.undercloud_ssh_client()
            self.add_node(address=config.hostname,
                          group='undercloud',
                          ssh_client=ssh_client)

    def discover_overcloud_nodes(self):
        if _overcloud.has_overcloud():
            for server in _overcloud.list_overcloud_nodes():
                try:
                    _overcloud.power_on_overcloud_node(server)
                except Exception:
                    LOG.exception("Error ensuring overcloud node power "
                                  "status is on")
                host_config = _overcloud.overcloud_host_config(server=server)
                ssh_client = _overcloud.overcloud_ssh_client(
                    hostname=server.name,
                    host_config=host_config)
                node = self.add_node(address=host_config.hostname,
                                     hostname=server.name,
                                     group='overcloud',
                                     ssh_client=ssh_client)
                assert isinstance(node, TripleoTopologyNode)
                node.overcloud_server = server
                self.discover_overcloud_node_subgroups(node)

    def discover_overcloud_node_subgroups(self, node):
        # set of subgroups extracted from node name
        subgroups: typing.Set[str] = set()

        # extract subgroups names from node name
        subgroups.update(subgroup
                         for subgroup in node.name.split('-')
                         if is_valid_overcloud_group_name(group_name=subgroup,
                                                          node_name=node.name))

        # add all those known subgroups names that are contained in
        # the node name (controller, compute, ...)
        subgroups.update(subgroup
                         for subgroup in self.known_subgroups
                         if subgroup in node.name)

        # bind node to discovered subgroups
        if subgroups:
            for subgroup in sorted(subgroups):
                LOG.debug("Add node '%s' to subgroup '%s'", node.name,
                          subgroup)
                self.add_node(hostname=node.name, group=subgroup)
        else:
            LOG.warning("Unable to obtain any node subgroup from node "
                        "name: '%s'", node.name)
        return subgroups


class TripleoTopologyNode(topology.OpenStackTopologyNode):

    overcloud_server: typing.Optional[nova.NovaServer] = None

    def power_on_overcloud_node(self):
        server = self.overcloud_server
        if server is None:
            raise TypeError(f"Node {self.name} is not and Overcloud server")
        self.ssh_client.close()
        LOG.debug(f"Ensuring overcloud node {self.name} power is on...")
        _overcloud.power_on_overcloud_node(server)
        hostname = sh.get_hostname(ssh_client=self.ssh_client)
        LOG.debug(f"Overcloud node {self.name} power is on ("
                  f"hostname={hostname})")

    def power_off_overcloud_node(self):
        server = self.overcloud_server
        if server is None:
            raise TypeError(f"Node {self.name} is not and Overcloud server")
        self.ssh_client.close()
        LOG.debug(f"Ensuring overcloud node {self.name} power is off...")
        _overcloud.power_off_overcloud_node(server)
        LOG.debug(f"Overcloud server node {self.name} power is off.")


def is_valid_overcloud_group_name(group_name: str, node_name: str = None):
    if not group_name:
        return False
    if group_name in ['overcloud', node_name]:
        return False
    if is_number(group_name):
        return False
    return True


def is_number(text: str):
    try:
        float(text)
    except ValueError:
        return False
    else:
        return True


def setup_tripleo_topology():
    if _undercloud.has_undercloud() or _overcloud.has_overcloud():
        topology.set_default_openstack_topology_class(TripleoTopology)


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


def actual_node_groups(groups):
    """return only existing node groups"""
    return set(groups).intersection(topology.list_openstack_node_groups())


def get_node(node_name):
    node_name = node_name.split('.')[0]
    return [node for node in topology.list_openstack_nodes() if
            node.name == node_name][0]


def is_composable_roles_env():
    composable_nodes = ['messaging', 'database', 'networker']
    for nodes in composable_nodes:
        if nodes in topology.list_openstack_node_groups():
            return True
    return False
