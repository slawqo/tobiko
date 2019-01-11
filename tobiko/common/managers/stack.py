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
from __future__ import absolute_import

import os
import time

from heatclient.common import template_utils
from heatclient import exc
from oslo_log import log
import yaml

from tobiko.common import constants
from tobiko.common import exceptions


LOG = log.getLogger(__name__)


# Status
CREATE_IN_PROGRESS = 'CREATE_IN_PROGRESS'
CREATE_COMPLETE = 'CREATE_COMPLETE'
CREATE_FAILED = 'CREATE_FAILED'
DELETE_IN_PROGRESS = 'DELETE_IN_PROGRESS'
DELETE_COMPLETE = 'DELETE_COMPLETE'
DELETE_FAILED = 'DELETE_FAILED'


class StackManager(object):
    """Manages Heat stacks."""

    def __init__(self, client_manager, templates_dir, wait_interval=5):
        self.client = client_manager.heat_client
        self.templates_dir = templates_dir
        self.wait_interval = wait_interval

    def load_template(self, template_path):
        """Loads template from a given file."""
        _, template = template_utils.get_template_contents(template_path)
        return yaml.safe_dump(template)

    def create_stack(self, stack_name, template_name, parameters, wait=True):
        """Creates stack based on passed parameters."""
        stack = self.wait_for_stack_status(
            stack_name=stack_name, expected_status={DELETE_COMPLETE,
                                                    CREATE_COMPLETE,
                                                    CREATE_FAILED})
        if stack and stack.stack_status == CREATE_COMPLETE:
            LOG.debug('Stack %r already exists.', stack_name)
            return stack

        if stack and stack.stack_status.endswith('_FAILED'):
            self.delete_stack(stack_name, wait=True)

        template = self.load_template(os.path.join(self.templates_dir,
                                                   template_name))

        try:
            self.client.stacks.create(stack_name=stack_name,
                                      template=template,
                                      parameters=parameters)
        except exc.HTTPConflict:
            LOG.debug('Stack %r already exists.', stack_name)
        else:
            LOG.debug('Crating stack %r...', stack_name)

        if wait:
            return self.wait_for_stack_status(stack_name=stack_name)
        else:
            return self.get_stack(stack_name=stack_name)

    def delete_stack(self, stack_name, wait=False):
        """Deletes stack."""
        self.client.stacks.delete(stack_name)
        if wait:
            self.wait_for_stack_status(stack_name,
                                       expected_status={DELETE_COMPLETE})

    def get_stack(self, stack_name, resolve_outputs=False):
        """Returns stack ID."""
        try:
            return self.client.stacks.get(stack_name,
                                          resolve_outputs=resolve_outputs)
        except exc.HTTPNotFound:
            return None

    def wait_for_resource_status(self, stack_id, resource_name,
                                 status=CREATE_COMPLETE):
        """Waits for resource to reach the given status."""
        res = self.client.resources.get(stack_id, resource_name)
        while (res.resource_status != status):
            time.sleep(self.wait_interval)
            res = self.client.resources.get(stack_id, resource_name)

    def wait_for_stack_status(self, stack_name=None, stack=None,
                              expected_status=None, check=True):
        """Waits for the stack to reach the given status."""
        expected_status = expected_status or {CREATE_COMPLETE}
        stack_name = stack_name or stack.stack_name
        stack = stack or self.get_stack(stack_name=stack_name)
        while (stack and stack.stack_status.endswith('_IN_PROGRESS') and
               stack.stack_status not in expected_status):
            LOG.debug("Waiting for %r stack status (observed=%r, expected=%r)",
                      stack_name, stack.stack_status, expected_status)
            time.sleep(self.wait_interval)
            stack = self.get_stack(stack_name=stack_name)

        if check:
            if stack is None:
                if DELETE_COMPLETE not in expected_status:
                    raise StackNotFound(name=stack_name)
            else:
                check_stack_status(stack, expected_status)
        return stack

    def get_output(self, stack, key):
        """Returns a specific value from stack outputs by using a given key."""
        check_stack_status(stack, {CREATE_COMPLETE})
        if not hasattr(stack, 'outputs'):
            stack = self.get_stack(stack_name=stack.stack_name,
                                   resolve_outputs=True)
        outputs = {output['output_key']: output['output_value']
                   for output in stack.outputs}
        try:
            return outputs[key]
        except KeyError:
            raise InvalidOutputKey(name=stack.stack_name,
                                   key=key)

    def get_templates_names(self, strip_suffix=False):
        """Returns a list of all the files in templates dir."""
        templates = []
        for (_, _, files) in os.walk(self.templates_dir):
            templates.extend(files)
        if strip_suffix:
            templates = [
                f[:-len(constants.TEMPLATE_SUFFIX)] for f in templates]
        return templates

    def get_stacks_match_templates(self):
        """Returns a list of existing stack names in the cloud project
        which match the templates defined in the project source code."""
        matched_stacks = []

        code_stacks = self.get_templates_names(strip_suffix=True)
        cloud_stacks = self.client.stacks.list()

        for stack in cloud_stacks:
            if stack.stack_name in code_stacks:
                matched_stacks.append(stack.stack_name)

        return matched_stacks


def check_stack_status(stack, expected):
    observed = stack.stack_status
    if observed not in expected:
        if observed == CREATE_FAILED:
            error_class = StackCreationFailed
        elif observed == DELETE_FAILED:
            error_class = StackDeletionFailed
        else:
            error_class = InvalidStackStatus
        raise error_class(name=stack.stack_name,
                          observed=observed,
                          expected=expected,
                          reason=stack.stack_status_reason)


class InvalidOutputKey(exceptions.TobikoException):
    msg = ("Output key %(key)r not found in stack %(name).")


class StackNotFound(exceptions.TobikoException):
    msg = ("Stack %(name)r not found")


class InvalidStackStatus(exceptions.TobikoException):
    msg = ("Stack %(name)r status %(observed)r not in %(expected)r "
           "(reason=%(status_reason)r)")


class StackCreationFailed(InvalidStackStatus):
    pass


class StackDeletionFailed(InvalidStackStatus):
    pass
