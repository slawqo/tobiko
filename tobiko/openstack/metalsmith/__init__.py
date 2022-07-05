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

from tobiko.openstack.metalsmith import _client
from tobiko.openstack.metalsmith import _instance


CLIENT_CLASSES = _client.CLIENT_CLASSES
MetalsmithClient = _client.MetalsmithClient
MetalsmithClientFixture = _client.MetalsmithClientFixture
MetalsmithClientType = _client.MetalsmithClientType
metalsmith_client = _client.metalsmith_client
get_metalsmith_client = _client.get_metalsmith_client

MetalsmithInstance = _instance.MetalsmithInstance
list_instances = _instance.list_instances
find_instance = _instance.find_instance
list_instance_ip_addresses = _instance.list_instance_ip_addresses
find_instance_ip_address = _instance.find_instance_ip_address
