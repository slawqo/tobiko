# Copyright 2020 Red Hat
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

from tobiko.tripleo import _ansible
from tobiko.tripleo import _overcloud as overcloud
from tobiko.tripleo import _topology as topology
from tobiko.tripleo import _undercloud as undercloud


get_tripleo_ansible_inventory = _ansible.get_tripleo_ansible_inventory
get_tripleo_ansible_inventory_file = \
    _ansible.get_tripleo_ansible_inventory_file
has_tripleo_ansible_inventory = _ansible.has_tripleo_ansible_inventory
read_tripleo_ansible_inventory = _ansible.read_tripleo_ansible_inventory
skip_if_missing_tripleo_ansible_inventory = \
    _ansible.skip_if_missing_tripleo_ansible_inventory

find_overcloud_node = overcloud.find_overcloud_node
list_overcloud_nodes = overcloud.list_overcloud_nodes
load_overcloud_rcfile = overcloud.load_overcloud_rcfile
overcloud_host_config = overcloud.overcloud_host_config
overcloud_node_ip_address = overcloud.overcloud_node_ip_address
overcloud_ssh_client = overcloud.overcloud_ssh_client
skip_if_missing_overcloud = overcloud.skip_if_missing_overcloud

TripleoTopology = topology.TripleoTopology

load_undercloud_rcfile = undercloud.load_undercloud_rcfile
has_undercloud = undercloud.has_undercloud
skip_if_missing_undercloud = undercloud.skip_if_missing_undercloud
undercloud_host_config = undercloud.undercloud_host_config
undercloud_keystone_client = undercloud.undercloud_keystone_client
undercloud_keystone_credentials = undercloud.undercloud_keystone_credentials
undercloud_keystone_session = undercloud.undercloud_keystone_session
undercloud_ssh_client = undercloud.undercloud_ssh_client
