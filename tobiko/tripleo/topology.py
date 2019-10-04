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


from tobiko.openstack import topology
from tobiko.tripleo import overcloud
from tobiko.tripleo import undercloud


class TripleoTopology(topology.OpenStackTopology):

    def discover_nodes(self):
        self.discover_undercloud_nodes()
        self.discover_overcloud_nodes()
        super(TripleoTopology, self).discover_nodes()

    def discover_undercloud_nodes(self):
        if undercloud.has_undercloud():
            config = undercloud.undercloud_host_config()
            ssh_client = undercloud.undercloud_ssh_client()
            self.add_node(address=config.hostname,
                          group_names=['undercloud'],
                          ssh_client=ssh_client)

    def discover_overcloud_nodes(self):
        if overcloud.has_overcloud():
            for server in overcloud.list_overcloud_nodes():
                config = overcloud.overcloud_host_config(server.name)
                ssh_client = overcloud.overcloud_ssh_client(server.name)
                self.add_node(address=config.hostname,
                              group_names=['overcloud'],
                              ssh_client=ssh_client)
