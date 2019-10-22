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

import collections
import weakref
import socket

import netaddr
from oslo_log import log
import six
from six.moves.urllib import parse

import tobiko
from tobiko.shell import ip
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.shell import ssh
from tobiko.openstack import nova
from tobiko.openstack import keystone
from tobiko.openstack.topology import _exception


LOG = log.getLogger(__name__)


DEFAULT_TOPOLOGY_CLASS = (
    'tobiko.openstack.topology._topology.OpenStackTopology')


def get_openstack_topology(topology_class=None):
    topology_class = topology_class or get_default_openstack_topology_class()
    return tobiko.setup_fixture(topology_class)


def list_openstack_nodes(topology=None, group=None, hostnames=None, **kwargs):
    topology = topology or get_openstack_topology()
    if group:
        nodes = topology.get_group(group=group)
    else:
        nodes = topology.nodes
    if hostnames:
        names = {node_name_from_hostname(hostname)
                 for hostname in hostnames}
        nodes = [node
                 for node in nodes
                 if node.name in names]
    if kwargs:
        nodes = nodes.with_attributes(**kwargs)
    return nodes


def find_openstack_node(topology=None, unique=False, **kwargs):
    nodes = list_openstack_nodes(topology=topology, **kwargs)
    if unique:
        return nodes.unique
    else:
        return nodes.first


def get_openstack_node(hostname, address=None, topology=None):
    topology = topology or get_openstack_topology()
    return topology.get_node(hostname=hostname, address=address)


def list_openstack_node_groups(topology=None):
    topology = topology or get_openstack_topology()
    return topology.groups


def get_default_openstack_topology_class():
    return DEFAULT_TOPOLOGY_CLASS


def set_default_openstack_topology_class(topology_class):
    # pylint: disable=global-statement
    global DEFAULT_TOPOLOGY_CLASS
    DEFAULT_TOPOLOGY_CLASS = topology_class


class OpenStackTopologyNode(object):

    def __init__(self, topology, name, public_ip, ssh_client):
        self._topology = weakref.ref(topology)
        self.name = name
        self.public_ip = public_ip
        self.ssh_client = ssh_client
        self.groups = set()

    @property
    def topology(self):
        return self._topology()

    def add_group(self, group):
        self.groups.add(group)

    @property
    def ssh_parameters(self):
        return self.ssh_client.setup_connect_parameters()

    def __repr__(self):
        return "{cls!s}<name={name!r}>".format(cls=type(self).__name__,
                                               name=self.name)


class OpenStackTopologyConfig(tobiko.SharedFixture):

    conf = None

    def setup_fixture(self):
        from tobiko import config
        CONF = config.CONF
        self.conf = CONF.tobiko.topology


class OpenStackTopology(tobiko.SharedFixture):

    config = tobiko.required_setup_fixture(OpenStackTopologyConfig)

    def __init__(self):
        super(OpenStackTopology, self).__init__()
        self._reachable_ips = set()
        self._unreachable_ips = set()
        self._nodes_by_name = collections.OrderedDict()
        self._nodes_by_ips = collections.OrderedDict()
        self._nodes_by_group = collections.OrderedDict()

    def setup_fixture(self):
        self.discover_nodes()

    def cleanup_fixture(self):
        self._reachable_ips.clear()
        self._unreachable_ips.clear()
        self._nodes_by_name.clear()
        self._nodes_by_ips.clear()
        self._nodes_by_group.clear()

    def discover_nodes(self):
        self.discover_configured_nodes()
        self.discover_controller_nodes()
        self.discover_compute_nodes()

    def discover_configured_nodes(self):
        for address in self.config.conf.nodes or []:
            self.add_node(address=address)

    def discover_controller_nodes(self):
        endpoints = keystone.list_endpoints(interface='public')
        addresses = set(parse.urlparse(endpoint.url).hostname
                        for endpoint in endpoints)
        for address in addresses:
            self.add_node(address=address, group='controller')

    def discover_compute_nodes(self):
        for hypervisor in nova.list_hypervisors():
            self.add_node(hostname=hypervisor.hypervisor_hostname,
                          address=hypervisor.host_ip,
                          group='compute')

    def add_node(self, hostname=None, address=None, group=None,
                 ssh_client=None):
        name = hostname and node_name_from_hostname(hostname) or None
        ips = set()
        if address:
            ips.update(self._ips(address))
        if hostname:
            ips.update(self._ips(hostname))
        ips = tobiko.select(ips)

        try:
            node = self.get_node(name=name, address=ips)
        except _exception.NoSuchOpenStackTopologyNode:
            node = self._add_node(hostname=hostname, ips=ips,
                                  ssh_client=ssh_client)

        if node and group:
            self.add_group(group=group).append(node)
            node.add_group(group=group)
        return node

    def _add_node(self, ips, hostname=None, ssh_client=None):
        public_ip = self._public_ip(ips, ssh_client=ssh_client)
        if public_ip is None:
            LOG.debug("Unable to SSH connect to any node IP address: %s"
                      ','.join(str(ip_address) for ip_address in ips))
            return None

        # I need to get a name for the new node
        ssh_client = ssh_client or self._ssh_client(public_ip)
        hostname = hostname or sh.get_hostname(ssh_client=ssh_client)
        name = node_name_from_hostname(hostname)
        try:
            node = self._nodes_by_name[name]
        except KeyError:
            self._nodes_by_name[name] = node = self.create_node(
                name=name, public_ip=public_ip, ssh_client=ssh_client)
            other = self._nodes_by_ips.setdefault(public_ip, node)
            if node is not other:
                LOG.error("Two nodes have the same IP address (%s): %r, %r",
                          public_ip, node.name, other.name)
        return node

    def get_node(self, name=None, hostname=None, address=None):
        name = name or (hostname and node_name_from_hostname(hostname))
        details = {}
        if name:
            tobiko.check_valid_type(name, six.string_types)
            details['name'] = name
            try:
                return self._nodes_by_name[name]
            except KeyError:
                pass
        if address:
            details['address'] = address
            for ip_address in self._ips(address):
                try:
                    return self._nodes_by_ips[ip_address]
                except KeyError:
                    pass
        raise _exception.NoSuchOpenStackTopologyNode(details=details)

    def create_node(self, name, public_ip, ssh_client, **kwargs):
        return OpenStackTopologyNode(topology=self, name=name,
                                     public_ip=public_ip,
                                     ssh_client=ssh_client, **kwargs)

    @property
    def nodes(self):
        return tobiko.select(self.get_node(name)
                             for name in self._nodes_by_name)

    def add_group(self, group):
        try:
            return self._nodes_by_group[group]
        except KeyError:
            self._nodes_by_group[group] = nodes = self.create_group()
            return nodes

    def create_group(self):
        return tobiko.Selection()

    def get_group(self, group):
        try:
            return self._nodes_by_group[group]
        except KeyError:
            raise _exception.NoSuchOpenStackTopologyNodeGroup(group=group)

    @property
    def groups(self):
        return list(self._nodes_by_group)

    def _ssh_client(self, address, username=None, port=None,
                    key_filename=None, **ssh_parameters):
        username = username or self.config.conf.username
        port = port or self.config.conf.port
        key_filename = key_filename or self.config.conf.key_file
        return ssh.ssh_client(host=str(address),
                              username=username,
                              key_filename=key_filename,
                              **ssh_parameters)

    def _public_ip(self, ips, ssh_client=None):
        reachable_ip = self._reachable_ip(ips)
        if reachable_ip:
            return reachable_ip

        if not ssh_client:
            # Try connecting via other nodes to get target node IP
            # addresses
            proxy_client = None
            for proxy_node in self.nodes:
                proxy_client = proxy_node.ssh_client
                if proxy_client:
                    internal_ip = self._reachable_ip(ips,
                                                     proxy_client=proxy_client)
                    if internal_ip:
                        ssh_client = self._ssh_client(
                            internal_ip, proxy_client=proxy_client)
                        break
                if ssh_client:
                    break

        if ssh_client:
            # Connect via SSH to to get target node IP addresses
            ips = self._ips_from_host(ssh_client=ssh_client)
            reachable_ip = self._reachable_ip(ips)
            if reachable_ip:
                return reachable_ip

        LOG.warning('Unable to reach remote host via any IP address: %s',
                    ', '.join(str(a) for a in ips))
        return None

    def _reachable_ip(self, ips, proxy_client=None, **kwargs):
        reachable = None
        if proxy_client:
            untested_ips = ips
        else:
            # Exclude unreachable addresses
            untested_ips = list()
            for address in ips:
                if address not in self._unreachable_ips:
                    if address in self._reachable_ips:
                        # Will take result from the first one of marked already
                        # marked as reachable
                        reachable = reachable or address
                    else:
                        # Will later search for results between the other IPs
                        untested_ips.append(address)

        for address in untested_ips:
            if reachable is None:
                try:
                    received = ping.ping(address, count=1, timeout=5.,
                                         ssh_client=proxy_client,
                                         **kwargs).received
                except ping.PingFailed:
                    pass
                else:
                    if received:
                        reachable = address
                        # Mark IP as reachable
                        self._reachable_ips.add(address)
                        continue

            # Mark IP as unreachable
            self._unreachable_ips.add(address)

        return reachable

    @property
    def ip_version(self):
        ip_version = self.config.conf.ip_version
        return ip_version and int(ip_version) or None

    def _ips_from_host(self, **kwargs):
        return ip.list_ip_addresses(ip_version=self.ip_version,
                                    scope='global', **kwargs)

    def _ips(self, obj):
        if isinstance(obj, tobiko.Selection):
            ips = obj
        elif isinstance(obj, netaddr.IPAddress):
            ips = tobiko.select([obj])
        elif isinstance(obj, six.string_types):
            try:
                ips = tobiko.select([netaddr.IPAddress(obj)])
            except (netaddr.AddrFormatError, ValueError):
                try:
                    addrinfo = socket.getaddrinfo(
                        obj, 22, 0, 0,
                        socket.AI_CANONNAME | socket.IPPROTO_TCP)
                except socket.gaierror:
                    ips = tobiko.select([])
                else:
                    ips = tobiko.select([
                        netaddr.IPAddress(sockaddr[0])
                        for _, _, _, _, sockaddr in addrinfo])
        else:
            for item in iter(obj):
                tobiko.check_valid_type(item, netaddr.IPAddress)
            ips = tobiko.select(obj)

        if ips and self.ip_version:
            ips = ips.with_attributes(version=self.ip_version)
        return ips


def node_name_from_hostname(hostname):
    return hostname.split('.', 1)[0].lower()
