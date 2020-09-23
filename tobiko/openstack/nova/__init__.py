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
from tobiko.openstack.nova import _cloud_init
from tobiko.openstack.nova import _hypervisor
from tobiko.openstack.nova import _server
from tobiko.openstack.nova import _service


CLIENT_CLASSES = _client.CLIENT_CLASSES
get_console_output = _client.get_console_output
get_nova_client = _client.get_nova_client
get_server = _client.get_server
find_hypervisor = _client.find_hypervisor
find_server = _client.find_server
find_service = _client.find_service
HasNovaClientMixin = _client.HasNovaClientMixin
list_hypervisors = _client.list_hypervisors
list_servers = _client.list_servers
list_services = _client.list_services
nova_client = _client.nova_client
NovaClientFixture = _client.NovaClientFixture
wait_for_server_status = _client.wait_for_server_status
WaitForServerStatusError = _client.WaitForServerStatusError
WaitForServerStatusTimeout = _client.WaitForServerStatusTimeout
shutoff_server = _client.shutoff_server
activate_server = _client.activate_server
migrate_server = _client.migrate_server
confirm_resize = _client.confirm_resize

WaitForCloudInitTimeoutError = _cloud_init.WaitForCloudInitTimeoutError
cloud_config = _cloud_init.cloud_config
get_cloud_init_status = _cloud_init.get_cloud_init_status
user_data = _cloud_init.user_data
wait_for_cloud_init_done = _cloud_init.wait_for_cloud_init_done
wait_for_cloud_init_status = _cloud_init.wait_for_cloud_init_status

skip_if_missing_hypervisors = _hypervisor.skip_if_missing_hypervisors
get_same_host_hypervisors = _hypervisor.get_same_host_hypervisors
get_different_host_hypervisors = _hypervisor.get_different_host_hypervisors
get_server_hypervisor = _hypervisor.get_server_hypervisor
get_servers_hypervisors = _hypervisor.get_servers_hypervisors

find_server_ip_address = _server.find_server_ip_address
HasServerMixin = _server.HasServerMixin
list_server_ip_addresses = _server.list_server_ip_addresses

wait_for_services_up = _service.wait_for_services_up
