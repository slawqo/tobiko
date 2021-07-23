# Copyright 2021 Red Hat
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

import json
import typing

from oslo_log import log

from tobiko.openstack.topology import _topology
from tobiko.shell import ping


LOG = log.getLogger(__name__)


def assert_reachable_nodes(
        nodes: typing.Iterable[_topology.OpenStackTopologyNode],
        **ping_params):
    node_ips = {node.name: str(node.public_ip) for node in nodes}
    LOG.debug(f"Test nodes are reachable: "
              f"{json.dumps(node_ips, sort_keys=True, indent=4)}")
    ping.assert_reachable_hosts(node_ips.values(), **ping_params)


def assert_unreachable_nodes(
        nodes: typing.Iterable[_topology.OpenStackTopologyNode],
        **ping_params):
    node_ips = {node.name: str(node.public_ip) for node in nodes}
    LOG.debug(f"Test nodes are unreachable: "
              f"{json.dumps(node_ips, sort_keys=True, indent=4)}")
    ping.assert_unreachable_hosts(node_ips.values(), **ping_params)
