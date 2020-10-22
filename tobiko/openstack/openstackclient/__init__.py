# Copyright (c) 2020 Red Hat, Inc.
#
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

from tobiko.openstack.openstackclient import _exception
from tobiko.openstack.openstackclient import _client
from tobiko.openstack.openstackclient import _network
from tobiko.openstack.openstackclient import _port
from tobiko.openstack.openstackclient import _security_group
from tobiko.openstack.openstackclient import _security_group_rule
from tobiko.openstack.openstackclient import _subnet


OSPCliError = _exception.OSPCliAuthError
OSPCliAuthError = _exception.OSPCliAuthError

execute = _client.execute

network_list = _network.network_list
network_show = _network.network_show
network_create = _network.network_create
network_delete = _network.network_delete
network_set = _network.network_set
network_unset = _network.network_unset

port_list = _port.port_list
port_show = _port.port_show
port_create = _port.port_create
port_delete = _port.port_delete
port_set = _port.port_set
port_unset = _port.port_unset

security_group_list = _security_group.security_group_list
security_group_show = _security_group.security_group_show
security_group_create = _security_group.security_group_create
security_group_delete = _security_group.security_group_delete
security_group_set = _security_group.security_group_set
security_group_unset = _security_group.security_group_unset

security_group_rule_list = _security_group_rule.security_group_rule_list
security_group_rule_show = _security_group_rule.security_group_rule_show
security_group_rule_create = _security_group_rule.security_group_rule_create
security_group_rule_delete = _security_group_rule.security_group_rule_delete

subnet_list = _subnet.subnet_list
subnet_show = _subnet.subnet_show
subnet_create = _subnet.subnet_create
subnet_delete = _subnet.subnet_delete
subnet_set = _subnet.subnet_set
subnet_unset = _subnet.subnet_unset
