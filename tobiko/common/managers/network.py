# Copyright 2018 Red Hat
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


class NetworkManager(object):
    """Manages Neutron Resources."""

    def __init__(self, client_manager):
        self.client = client_manager.neutron_client

    def create_sg_rules(self, rules, sg_id):
        """Creates security group rules."""
        for rule in rules:
            rule['security_group_id'] = sg_id
            body = {'security_group_rule': rule}
            self.client.create_security_group_rule(body)
