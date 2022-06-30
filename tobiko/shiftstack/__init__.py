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

from tobiko.shiftstack import _clouds_file
from tobiko.shiftstack import _neutron
from tobiko.shiftstack import _nova
from tobiko.shiftstack import _skip

ShiftStackCloudsFileFixture = _clouds_file.ShiftStackCloudsFileFixture
get_clouds_file_path = _clouds_file.get_clouds_file_path

list_shiftstack_node_ip_addresses = _neutron.list_shiftstack_node_ip_addresses
find_shiftstack_node_ip_address = _neutron.find_shiftstack_node_ip_address

find_shiftstack_node = _nova.find_shiftstack_node
list_shiftstack_nodes = _nova.list_shiftstack_nodes

skip_unless_has_shiftstack = _skip.skip_unless_has_shiftstack
