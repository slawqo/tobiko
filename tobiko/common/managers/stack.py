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
from heatclient import exc as heat_exc
import yaml

from tobiko.common import constants


class StackManager(object):
    """Manages Heat stacks."""

    def __init__(self, client_manager, templates_dir,
                 wait_interval=5):
        self.client = client_manager.get_heat_client()
        self.templates_dir = templates_dir
        self.wait_interval = wait_interval

    def load_template(self, template_path):
        """Loads template from a given file."""
        _files, template = template_utils.get_template_contents(template_path)
        return yaml.safe_dump(template)

    def create_stack(self, stack_name, template_name, parameters,
                     status=constants.COMPLETE_STATUS):
        """Creates stack based on passed parameters."""
        template = self.load_template(os.path.join(self.templates_dir,
                                                   template_name))

        stack = self.client.stacks.create(stack_name=stack_name,
                                          template=template,
                                          parameters=parameters)
        self.wait_for_stack_status(stack_name, status)

        return stack

    def delete_stack(self, sid):
        """Deletes stack."""
        self.client.stacks.delete(sid)

    def get_stack(self, stack_name):
        """Returns stack ID."""
        try:
            return self.client.stacks.get(stack_name)
        except heat_exc.HTTPNotFound:
            return

    def wait_for_resource_status(self, stack_id, resource_name,
                                 status="CREATE_COMPLETE"):
        """Waits for resource to reach the given status."""
        res = self.client.resources.get(stack_id, resource_name)
        while (res.resource_status != status):
            time.sleep(self.wait_interval)
            res = self.client.resources.get(stack_id, resource_name)

    def get_output(self, stack_name, index=0):
        """Returns the output from the given stack by using the given index."""
        stack = self.get_stack(stack_name=stack_name)
        output = stack.outputs[index]['output_value']
        return output

    def wait_for_stack_status(self, stack_name,
                              status=constants.COMPLETE_STATUS):
        """Waits for the stack to reach the given status."""
        stack = self.get_stack(stack_name=stack_name)
        while (stack.stack_status != status):
            time.sleep(self.wait_interval)
            stack = self.get_stack(stack_name=stack_name)
