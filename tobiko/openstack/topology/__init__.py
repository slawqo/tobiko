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

from tobiko.openstack.topology import _exception
from tobiko.openstack.topology import _topology


NoSuchOpenStackTopologyNodeGroup = _exception.NoSuchOpenStackTopologyNodeGroup
NoSuchOpenStackTopologyNode = _exception.NoSuchOpenStackTopologyNode

get_openstack_topology = _topology.get_openstack_topology
get_default_openstack_topology_class = (
    _topology.get_default_openstack_topology_class)
OpenStackTopology = _topology.OpenStackTopology
set_default_openstack_topology_class = (
    _topology.set_default_openstack_topology_class)
