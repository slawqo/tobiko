# Copyright 2022 Red Hat
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
import typing

import tobiko
from tobiko.openstack.topology import _topology
from tobiko.shell import ip


def get_hosts_namespaces(hostnames: typing.Iterable[str] = None,
                         **params) \
        -> typing.Dict[str, typing.List[str]]:
    if isinstance(hostnames, str):
        hostnames = [hostnames]
    namespaces = collections.defaultdict(list)
    nodes = _topology.list_openstack_nodes(hostnames=hostnames,
                                           **params)
    for node in nodes:
        for namespace in ip.list_network_namespaces(
                ssh_client=node.ssh_client):
            namespaces[namespace].append(node.hostname)
    return namespaces


def assert_namespace_in_hosts(namespace: str,
                              hostnames: typing.Iterable[str] = None,
                              **params):
    namespaces = get_hosts_namespaces(hostnames=hostnames, **params)
    actual_hostnames = set(_hostname
                           for _hostnames in namespaces.values()
                           for _hostname in _hostnames)
    tobiko.get_test_case().assertIn(
        namespace, set(namespaces),
        f"Namespace {namespace!r} not in hosts {actual_hostnames!r}")


def assert_namespace_not_in_hosts(namespace: str,
                                  hostnames: typing.Iterable[str] = None,
                                  **params):
    namespaces = get_hosts_namespaces(hostnames=hostnames, **params)
    actual_hostnames = namespaces.get(namespace)
    tobiko.get_test_case().assertNotIn(
        namespace, set(namespaces),
        f"Namespace {namespace!r} in hosts: {actual_hostnames!r}")
