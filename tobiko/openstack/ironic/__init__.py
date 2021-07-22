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

from tobiko.openstack.ironic import _client
from tobiko.openstack.ironic import _node

get_ironic_client = _client.get_ironic_client

power_off_node = _node.power_off_node
power_on_node = _node.power_on_node
IronicNodeType = _node.IronicNodeType
WaitForNodePowerStateError = _node.WaitForNodePowerStateError
WaitForNodePowerStateTimeout = _node.WaitForNodePowerStateTimeout
