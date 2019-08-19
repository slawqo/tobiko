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

from tobiko.openstack.nova import _client
from tobiko.openstack.nova import _hypervisor


CLIENT_CLASSES = _client.CLIENT_CLASSES
get_nova_client = _client.get_nova_client
list_hypervisors = _client.list_hypervisors
nova_client = _client.nova_client
NovaClientFixture = _client.NovaClientFixture
find_hypervisor = _client.find_hypervisor
get_console_output = _client.get_console_output

get_server = _client.get_server

skip_if_missing_hypervisors = _hypervisor.skip_if_missing_hypervisors
