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
import os
import time

from heatclient.common import template_utils
import yaml


class StackManager(object):
    """Manages Heat stacks."""

    def __init__(self, client_manager, templates_dir):
        self.client = client_manager.get_heat_client()
        self.templates_dir = templates_dir

    def load_template(self, template_path):
        """Loads template from a given file."""
        _files, template = template_utils.get_template_contents(template_path)
        return yaml.safe_dump(template)

    def create_stack(self, stack_name, template_name, parameters):
        """Creates stack based on passed parameters."""
        template = self.load_template(os.path.join(self.templates_dir,
                                                   template_name))

        stack = self.client.stacks.create(stack_name=stack_name,
                                          template=template,
                                          parameters=parameters)

        return stack

    def delete_stack(self, sid):
        """Deletes stack."""
        self.client.stacks.delete(sid)

    def get_stack(self, stack_name):
        """Returns stack ID."""
        return self.client.stacks.get(stack_name)

    def wait_for_status_complete(self, stack_id, resource_name):
        """Verifies resource reached complete status.

        If it didn't, the method will wait until resource reaches
        complete status or when timeout reached.
        """
        res = self.client.resources.get(stack_id, resource_name)
        while (res.resource_status != 'CREATE_COMPLETE'):
            time.sleep(5)
            res = self.client.resources.get(stack_id, resource_name)
