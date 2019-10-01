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

import weakref
import socket

import netaddr
from oslo_log import log

import tobiko
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.shell import ssh
from tobiko.openstack import nova
from tobiko.openstack.topology import _exception

LOG = log.getLogger(__name__)


def get_openstack_topology(topology_class=None):
    topology_class = topology_class or DEFAULT_TOPOLOGY_CLASS
    return tobiko.setup_fixture(DEFAULT_TOPOLOGY_CLASS)


def list_openstack_nodes():
    return get_openstack_topology().nodes


def list_openstack_node_groups():
    return get_openstack_topology().groups


def get_default_openstack_topology_class():
    return DEFAULT_TOPOLOGY_CLASS


def set_default_openstack_topology_class(topology_class):
    # pylint: disable=global-statement
    global DEFAULT_TOPOLOGY_CLASS
    if not issubclass(topology_class, OpenStackTopology):
        message = "{!r} is not subclass of OpenStackTopology".format(
            topology_class)
        raise TypeError(message)
    DEFAULT_TOPOLOGY_CLASS = topology_class


class OpenStackTopologyElement(object):

    def __init__(self, topology, name):
        self._topology = weakref.ref(topology)
        self.name = name

    @property
    def topology(self):
        return self._topology()

    def __repr__(self):
        return "{cls!s}(topology={topology!r}, name={name!r})".format(
            cls=type(self).__name__,
            topology=self.topology,
            name=self.name)


class OpenStackTopologyNode(OpenStackTopologyElement):

    def __init__(self, topology, name, ssh_client=None):
        super(OpenStackTopologyNode, self).__init__(topology=topology,
                                                    name=name)
        self._addresses = list()
        self._groups = set()
        self._ssh_client = ssh_client

    def add_group(self, name):
        self._groups.add(name)

    @property
    def groups(self):
        return tobiko.select(self.topology.get_group(name)
                             for name in sorted(self._groups))

    def add_address(self, address):
        self._addresses.append(netaddr.IPAddress(address))

    @property
    def addresses(self):
        return tobiko.select(address
                             for address in self._addresses)

    @property
    def ssh_client(self):
        ssh_client = self._ssh_client
        if ssh_client is None:
            self._ssh_client = ssh_client = self.topology.get_ssh_client(
                host=self.addresses.first)
        return ssh_client


class OpenStackTopologyNodeGroup(OpenStackTopologyElement):

    def __init__(self, topology, name):
        super(OpenStackTopologyNodeGroup, self).__init__(topology=topology,
                                                         name=name)
        self._nodes = set()

    def add_node(self, name):
        self._nodes.add(name)

    @property
    def nodes(self):
        return tobiko.select(self.topology.get_node(name)
                             for name in sorted(self._nodes))


class OpenStackTopologyConfig(tobiko.SharedFixture):

    conf = None

    def setup_fixture(self):
        from tobiko import config
        CONF = config.CONF
        self.conf = CONF.tobiko.topology


class OpenStackTopology(tobiko.SharedFixture):

    _nodes = None
    _groups = None
    config = tobiko.required_setup_fixture(OpenStackTopologyConfig)

    def setup_fixture(self):
        self.clear_nodes()
        self.discover_nodes()

    def clear_nodes(self):
        self._nodes = {}
        self._groups = {}

    def discover_nodes(self):
        self.discover_configured_nodes()
        self.discover_compute_nodes()

    def discover_configured_nodes(self):
        for host in self.config.conf.nodes or []:
            self.add_node(address=host)

    def discover_compute_nodes(self):
        for hypervisor in nova.list_hypervisors():
            address = hypervisor.host_ip
            if not ping.ping(address).received:
                LOG.warning("Cannot reach hypervisor IP address %r from host "
                            "%r", hypervisor.host_ip, socket.gethostname())
                address = None
            self.add_node(address=address,
                          hostname=node_name_from_hostname(
                              hypervisor.hypervisor_hostname),
                          group_names=['compute'])

    def add_node(self, name=None, address=None, hostname=None,
                 group_names=None, ssh_client=None):
        name = name or self.get_node_name(hostname=hostname,
                                          address=address,
                                          ssh_client=ssh_client)
        node = self.create_node(name=name, ssh_client=ssh_client)
        if address:
            node.add_address(address=address)

        for group_name in group_names or []:
            self.add_group(name=group_name, node_names=[name])
        return node

    def create_node(self, name, **kwargs):
        try:
            return self.get_node(name=name)
        except _exception.NoSuchOpenStackTopologyNode:
            self._nodes[name] = node = self.new_node(name=name, **kwargs)
            return node

    def get_node(self, name):
        try:
            return self._nodes[name]
        except KeyError:
            raise _exception.NoSuchOpenStackTopologyNode(name=name)

    def new_node(self, name, **kwargs):
        return OpenStackTopologyNode(topology=self, name=name, **kwargs)

    @property
    def nodes(self):
        return tobiko.select(self.get_node(name)
                             for name in sorted(self._nodes))

    def get_ssh_client(self, host, username=None, port=None, key_filename=None,
                       **ssh_parameters):
        if not host:
            message = "Invalid host address: {!r}".format(host)
            raise ValueError(message)
        conf = self.config.conf
        return ssh.ssh_client(host=str(host),
                              username=(username or conf.username),
                              port=(port or conf.port),
                              key_filename=(key_filename or conf.key_file),
                              **ssh_parameters)

    def add_group(self, name, node_names=None):
        group = self.create_group(name=name)
        for node_name in node_names or []:
            group.add_node(name=node_name)
            self.get_node(name=node_name).add_group(name=name)

    def create_group(self, name):
        try:
            return self.get_group(name=name)
        except _exception.NoSuchOpenStackTopologyGroup:
            self._groups[name] = group = self.new_group(name=name)
            return group

    def get_group(self, name):
        try:
            return self._groups[name]
        except KeyError:
            raise _exception.NoSuchOpenStackTopologyGroup(name=name)

    def new_group(self, name):
        return OpenStackTopologyNodeGroup(topology=self, name=name)

    @property
    def groups(self):
        return tobiko.select(self.get_group(name)
                             for name in sorted(self._groups))

    def get_node_name(self, hostname=None, address=None, ssh_client=None):
        if address and not hostname:
            ssh_client = ssh_client or self.get_ssh_client(host=address)
            hostname = sh.get_hostname(ssh_client=ssh_client)
        if hostname:
            return node_name_from_hostname(hostname=hostname)

        message = ("Unable to get node name: hostname={!r}, "
                   "address={!r}").format(
            hostname, address)
        raise ValueError(message)


DEFAULT_TOPOLOGY_CLASS = OpenStackTopology


def node_name_from_hostname(hostname):
    return hostname.split('.', 1)[0].lower()
