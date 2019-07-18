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

import collections
import time

from heatclient import exc
from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack.heat import _client
from tobiko.openstack.heat import _template


LOG = log.getLogger(__name__)

# Status
INIT_IN_PROGRESS = 'INIT_IN_PROGRESS'
INIT_COMPLETE = 'INIT_COMPLETE'
INIT_IN_PROGRESS = 'INIT_FAILED'
CREATE_IN_PROGRESS = 'CREATE_IN_PROGRESS'
CREATE_COMPLETE = 'CREATE_COMPLETE'
CREATE_FAILED = 'CREATE_FAILED'
DELETE_IN_PROGRESS = 'DELETE_IN_PROGRESS'
DELETE_COMPLETE = 'DELETE_COMPLETE'
DELETE_FAILED = 'DELETE_FAILED'


TEMPLATE_FILE_SUFFIX = '.yaml'


def _stack_parameters(obj, stack=None):
    if obj is None or isinstance(obj, collections.Mapping):
        parameters = HeatStackParametersFixture(stack, obj)
    else:
        parameters = tobiko.get_fixture(obj)
    if not isinstance(parameters, HeatStackParametersFixture):
        msg = "Object {!r} is not an HeatStackParametersFixture".format(
            parameters)
        raise TypeError(msg)
    return parameters


class HeatStackFixture(tobiko.SharedFixture):
    """Manages Heat stacks."""

    client = None
    retry_create_stack = 1
    wait_interval = 5
    stack_name = None
    template = None
    stack = None
    parameters = None

    def __init__(self, stack_name=None, template=None, parameters=None,
                 wait_interval=None, client=None):
        super(HeatStackFixture, self).__init__()
        self.stack_name = stack_name = (stack_name or
                                        self.stack_name or
                                        self.fixture_name)

        self.template = _template.heat_template(template or self.template)
        self.parameters = _stack_parameters(
            stack=self, obj=(parameters or self.parameters))
        self.client = client or self.client
        if config.get_bool_env('TOBIKO_PREVENT_CREATE'):
            self.retry_create_stack = 0

        if wait_interval:
            self.wait_interval = wait_interval

    def _get_retry_value(self, retry):
        if retry is None:
            retry = self.retry_create_stack
            if retry is None:
                retry = 1
        return int(retry)

    def setup_fixture(self):
        self.setup_template()
        self.setup_client()
        self.setup_stack()

    def setup_template(self):
        tobiko.setup_fixture(self.template)

    def setup_client(self):
        self.client = _client.heat_client(self.client)

    def setup_stack(self):
        self.create_stack()

    def get_stack_parameters(self):
        return tobiko.reset_fixture(self.parameters).values

    def create_stack(self, retry=None):
        """Creates stack based on passed parameters."""
        created_stack_ids = set()
        retry = self._get_retry_value(retry)
        while True:
            stack = self.wait_for_stack_status(
                expected_status={CREATE_COMPLETE, CREATE_FAILED,
                                 CREATE_IN_PROGRESS, DELETE_COMPLETE,
                                 DELETE_FAILED})
            stack_status = getattr(stack, 'stack_status', DELETE_COMPLETE)
            expected_status = {CREATE_COMPLETE, CREATE_IN_PROGRESS}
            if stack_status in expected_status:
                LOG.debug('Stack created: %r (id=%r)', self.stack_name,
                          stack.id)
                for stack_id in created_stack_ids:
                    if self.stack.id != stack_id:
                        LOG.warning("Concurrent stack creation: delete "
                                    "duplicated stack is %r (id=%r).",
                                    self.stack_name, stack_id)
                        self.delete_stack(stack_id)

                return stack

            if not retry:
                status_reason = getattr(stack, 'stack_status_reason', None)
                raise HeatStackCreationFailed(name=self.stack_name,
                                              observed=stack_status,
                                              expected=expected_status,
                                              status_reason=status_reason)

            retry -= 1
            if stack_status.endswith('_FAILED'):
                LOG.debug('Delete existing failed stack: %r (id=%r)',
                          self.stack_name, stack.id)
                self.delete_stack()
                stack = self.wait_for_stack_status(
                    expected_status={DELETE_COMPLETE})

            # Cleanup cached objects
            self.stack = self._outputs = self._resources = None

            # Compile template parameters
            parameters = self.get_stack_parameters()
            try:
                LOG.debug('Creating stack %r (re-tries left %d)...',
                          self.stack_name, retry)
                stack_id = self.client.stacks.create(
                    stack_name=self.stack_name,
                    template=self.template.template_yaml,
                    parameters=parameters)['stack']['id']
            except exc.HTTPConflict:
                LOG.debug('Stack %r already exists.', self.stack_name)
            else:
                created_stack_ids.add(stack_id)
                LOG.debug('Creating stack %r (id=%r)...', self.stack_name,
                          stack_id)

    _resources = None

    @tobiko.fixture_property
    def resources(self):
        resources = self._resources
        if not self._resources:
            self._resources = resources = HeatStackResourceFixture(self)
        return resources

    def cleanup_fixture(self):
        self.setup_client()
        self.cleanup_stack()

    def cleanup_stack(self):
        self.delete_stack()

    def delete_stack(self, stack_id=None):
        """Deletes stack."""
        if not stack_id:
            stack_id = self.stack_id
            self.stack = self._outputs = self._resources = None
        try:
            self.client.stacks.delete(stack_id)
        except exc.NotFound:
            LOG.debug('Stack already deleted: %r (id=%r)', self.stack_name,
                      stack_id)
        else:
            LOG.debug('Deleting stack %r (id=%r)...', self.stack_name,
                      stack_id)

    @property
    def stack_id(self):
        stack = self.stack
        if stack:
            return stack.id
        else:
            return self.stack_name

    def get_stack(self, resolve_outputs=False):
        """Returns stack ID."""
        try:
            self.stack = stack = self.client.stacks.get(
                self.stack_name, resolve_outputs=resolve_outputs)
        except exc.HTTPNotFound:
            self.stack = stack = None
        finally:
            self._outputs = None
        return stack

    def wait_for_create_complete(self, check=True):
        return self.wait_for_stack_status(expected_status={CREATE_COMPLETE},
                                          check=check)

    def wait_for_delete_complete(self, check=True):
        return self.wait_for_stack_status(expected_status={DELETE_COMPLETE},
                                          check=check)

    def wait_for_stack_status(self, expected_status, check=True):
        """Waits for the stack to reach the given status."""
        stack = self.stack or self.get_stack()
        while (stack and stack.stack_status.endswith('_IN_PROGRESS') and
               stack.stack_status not in expected_status):
            LOG.debug("Waiting for %r (id=%r) stack status "
                      "(observed=%r, expected=%r)", self.stack_name,
                      stack.id, stack.stack_status, expected_status)
            time.sleep(self.wait_interval)
            stack = self.get_stack()

        if check:
            if stack is None:
                if DELETE_COMPLETE not in expected_status:
                    raise HeatStackNotFound(name=self.stack_name)
            else:
                check_stack_status(stack, expected_status)
        return stack

    _outputs = None

    def get_stack_outputs(self):
        outputs = self._outputs
        if not outputs:
            self._outputs = outputs = HeatStackOutputsFixture(self)
        return outputs

    outputs = tobiko.fixture_property(get_stack_outputs)

    def __getattr__(self, name):
        try:
            return self.get_stack_outputs().get_value(name)
        except HeatStackOutputKeyError:
            pass
        message = "Object {!r} has no attribute {!r}".format(self, name)
        raise AttributeError(message)


class HeatStackKeyError(tobiko.TobikoException):
    message = "key {key!r} not found in stack {name!r}"


class HeatStackResourceKeyError(HeatStackKeyError):
    message = "resource key {key!r} not found in stack {name!r}"


class HeatStackParameterKeyError(HeatStackKeyError):
    message = "parameter key {key!r} not found in stack {name!r}"


class HeatStackOutputKeyError(HeatStackKeyError):
    message = "output key {key!r} not found in stack {name!r}"


class HeatStackNamespaceFixture(tobiko.SharedFixture):

    key_error = HeatStackKeyError
    _keys = None
    _values = None

    def __init__(self, stack):
        super(HeatStackNamespaceFixture, self).__init__()
        if not isinstance(stack, HeatStackFixture):
            message = "Object {!r} is not an HeatStackFixture".format(stack)
            raise TypeError(message)
        self.stack = stack

    def setup_fixture(self):
        self.setup_keys()
        self.setup_values()

    def setup_keys(self):
        keys = self._keys
        if keys is None:
            self._keys = keys = self.get_keys()
            self.addCleanup(self.cleanup_keys)
        return keys

    keys = tobiko.fixture_property(setup_keys)

    def get_keys(self):
        raise NotImplementedError

    def cleanup_keys(self):
        del self._keys

    def setup_values(self):
        values = self._values
        if values is None:
            self._values = values = self.get_values()
            self.addCleanup(self.cleanup_values)
        return values

    values = tobiko.fixture_property(setup_values)

    def get_values(self):
        raise NotImplementedError

    def cleanup_values(self):
        del self._values

    def get_value(self, key):
        # Match template outputs definition before getting value
        if key in self.keys:
            try:
                return self.values[key]
            except KeyError:
                LOG.error('Key %r not found in stack %r', key,
                          self.stack.stack_name)
        else:
            LOG.error('Key %r not found in template for stack %r', key,
                      self.stack.stack_name)
        raise self.key_error(name=self.stack.stack_name, key=key)

    def set_value(self, key, value):
        # Match template outputs definition before setting value
        if key in self.keys:
            self.values[key] = value
        else:
            LOG.error('Key %r not found in template for stack %r', key,
                      self.stack.stack_name)
        raise self.key_error(name=self.stack.stack_name, key=key)

    def __getattr__(self, name):
        try:
            return self.get_value(name)
        except self.key_error:
            pass
        message = "Object {!r} has no attribute {!r}".format(self, name)
        raise AttributeError(message)


class HeatStackParametersFixture(HeatStackNamespaceFixture):

    key_error = HeatStackParameterKeyError

    def __init__(self, stack, parameters=None):
        super(HeatStackParametersFixture, self).__init__(stack)
        self.parameters = parameters and dict(parameters) or {}

    def get_keys(self):
        template = tobiko.setup_fixture(self.stack.template)
        return frozenset(template.parameters or [])

    def get_values(self):
        values = dict(self.parameters)
        missing_keys = sorted(self.keys - set(values))
        for key in missing_keys:
            value = getattr(self.stack, key, None)
            if value is not None:
                values[key] = value
        return values


class HeatStackOutputsFixture(HeatStackNamespaceFixture):

    key_error = HeatStackOutputKeyError

    def get_keys(self):
        template = tobiko.setup_fixture(self.stack.template)
        return frozenset(template.outputs or [])

    def get_values(self):
        # Can't get output values before stack creation is complete
        self.stack.wait_for_create_complete()
        outputs = self.stack.get_stack(resolve_outputs=True).outputs
        return {o['output_key']: o['output_value']
                for o in outputs}


def check_stack_status(stack, expected):
    observed = stack.stack_status
    if observed not in expected:
        if observed == CREATE_FAILED:
            error_class = HeatStackCreationFailed
        elif observed == DELETE_FAILED:
            error_class = HeatStackDeletionFailed
        else:
            error_class = InvalidHeatStackStatus
        raise error_class(name=stack.stack_name,
                          observed=observed,
                          expected=expected,
                          status_reason=stack.stack_status_reason)


class HeatStackNotFound(tobiko.TobikoException):
    message = "stack {name!r} not found"


class InvalidHeatStackStatus(tobiko.TobikoException):
    message = ("stack {name!r} status {observed!r} not in {expected!r}\n"
               "{status_reason!s}")


class HeatStackCreationFailed(InvalidHeatStackStatus):
    pass


class HeatStackDeletionFailed(InvalidHeatStackStatus):
    pass


class HeatStackResourceFixture(HeatStackNamespaceFixture):

    key_error = HeatStackResourceKeyError

    def get_keys(self):
        template = tobiko.setup_fixture(self.stack.template)
        return frozenset(template.resources or [])

    def get_values(self):
        self.stack.wait_for_create_complete()
        client = self.stack.client
        resources = client.resources.list(self.stack.stack_id)
        return {r.resource_name: r for r in resources}

    @property
    def fixture_name(self):
        return self.stack_name + '.resources'
