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
import random
import time
import typing

from heatclient.v1 import stacks
from heatclient import exc
from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack.heat import _client
from tobiko.openstack.heat import _template
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import nova


LOG = log.getLogger(__name__)

# Status
INIT_IN_PROGRESS = 'INIT_IN_PROGRESS'
INIT_COMPLETE = 'INIT_COMPLETE'
INIT_FAILED = 'INIT_FAILED'
CREATE_IN_PROGRESS = 'CREATE_IN_PROGRESS'
CREATE_COMPLETE = 'CREATE_COMPLETE'
CREATE_FAILED = 'CREATE_FAILED'
DELETE_IN_PROGRESS = 'DELETE_IN_PROGRESS'
DELETE_COMPLETE = 'DELETE_COMPLETE'
DELETE_FAILED = 'DELETE_FAILED'


TEMPLATE_FILE_SUFFIX = '.yaml'


def heat_stack_parameters(obj,
                          stack: 'HeatStackFixture' = None) \
        -> 'HeatStackParametersFixture':
    if isinstance(obj, HeatStackParametersFixture):
        parameters = obj
    elif obj is None or isinstance(obj, collections.Mapping):
        parameters = HeatStackParametersFixture(stack, obj)
    else:
        parameters = tobiko.get_fixture(obj)
    tobiko.check_valid_type(parameters, HeatStackParametersFixture)
    if stack is not None and parameters.stack is None:
        parameters.stack = stack
    tobiko.check_valid_type(parameters.stack, type(None), HeatStackFixture)
    return parameters


@keystone.skip_unless_has_keystone_credentials()
class HeatStackFixture(tobiko.SharedFixture):
    """Manages Heat stacks."""

    client: _client.HeatClientType = None
    retry_create_stack = 1
    wait_interval: float = 5
    wait_timeout: float = 300.
    template: _template.HeatTemplateFixture
    stack: typing.Optional[stacks.Stack] = None
    stack_name: typing.Optional[str] = None
    parameters: typing.Optional['HeatStackParametersFixture'] = None
    project: typing.Optional[str] = None
    user: typing.Optional[str] = None

    def __init__(
            self,
            stack_name: str = None,
            template: _template.HeatTemplateFixture = None,
            parameters=None,
            wait_interval: tobiko.Seconds = None,
            client: _client.HeatClientType = None):
        super(HeatStackFixture, self).__init__()
        if stack_name is not None:
            self.stack_name = stack_name
        if template is not None:
            self.template = _template.heat_template(template)
        if parameters is None:
            parameters = self.parameters
        self.parameters = heat_stack_parameters(obj=parameters,
                                                stack=self)
        if client is not None:
            self.client = client
        if config.get_bool_env('TOBIKO_PREVENT_CREATE'):
            self.retry_create_stack = 0
        if wait_interval is not None:
            self.wait_interval = wait_interval

    def _get_retry_value(self, retry) -> int:
        if retry is None:
            retry = self.retry_create_stack
            if retry is None:
                retry = 1
        return int(retry)

    def setup_fixture(self):
        self.setup_stack_name()
        self.setup_template()
        self.setup_parameters()
        self.setup_client()
        self.setup_project()
        self.setup_user()
        self.setup_stack()

    def setup_template(self):
        tobiko.setup_fixture(self.template)

    def setup_parameters(self):
        self.get_stack_parameters()

    def setup_stack_name(self) -> str:
        stack_name = self.stack_name
        if stack_name is None:
            self.stack_name = stack_name = self.fixture_name
        return stack_name

    def setup_client(self) -> _client.HeatClient:
        client = self.client
        if not isinstance(client, _client.HeatClient):
            self.client = client = _client.heat_client(self.client)
        return client

    @property
    def session(self):
        return self.setup_client().http_client.session

    def setup_project(self):
        if self.project is None:
            self.project = keystone.get_project_id(session=self.session)

    def setup_user(self):
        if self.user is None:
            self.user = keystone.get_user_id(session=self.session)

    def setup_stack(self) -> stacks.Stack:
        return self.create_stack()

    def get_stack_parameters(self):
        return tobiko.reset_fixture(self.parameters).values

    retry_create_min_sleep = 0.1
    retry_create_max_sleep = 3.

    def create_stack(self, retry=None) -> stacks.Stack:
        for attempt in tobiko.retry(count=self._get_retry_value(retry),
                                    interval=0.):
            try:
                return self.try_create_stack()
            except tobiko.TobikoException:
                attempt.check_limits()
                # It uses a random time sleep to make conflicting concurrent
                # creations less probable to occur
                sleep_time = random_sleep_time(
                    min_time=self.retry_create_min_sleep,
                    max_time=self.retry_create_max_sleep)
                LOG.debug(f"Failed creating stack '{self.stack_name}' "
                          f"(attempt {attempt.number} of {attempt.count})."
                          f'It will retry after {sleep_time} seconds',
                          exc_info=1)
                time.sleep(sleep_time)

        raise RuntimeError("It is expected check_limits to re-raise"
                           "exception before reaching here")

    #: valid status expected to be the stack after exiting from create_stack
    # method
    expected_creted_status = {CREATE_IN_PROGRESS, CREATE_COMPLETE}

    def validate_created_stack(self):
        return self.wait_for_stack_status(
            expected_status=self.expected_creted_status,
            check=True)

    def try_create_stack(self):
        stack = self.wait_for_stack_status(
            expected_status={CREATE_COMPLETE, CREATE_FAILED,
                             CREATE_IN_PROGRESS, DELETE_COMPLETE,
                             DELETE_FAILED})

        stack_status = getattr(stack, 'stack_status', DELETE_COMPLETE)
        if stack_status in {CREATE_IN_PROGRESS, CREATE_COMPLETE}:
            LOG.debug(f"Stack already created (name='{self.stack_name}', "
                      f"id='{stack.id}').")
            return stack
        if stack_status.endswith('_FAILED'):
            LOG.debug('Delete existing failed stack: %r (id=%r)',
                      self.stack_name, stack.id)
            self.delete_stack(stack_id=stack.id)

        # Cleanup cached objects
        if stack is not None:
            self.wait_until_stack_deleted()
        assert self.stack is None
        self._outputs = self._resources = None

        # Re-compile template parameters
        parameters = self.get_stack_parameters()

        # Ensure quota limits are OK just in time before start creating
        # a new stack
        self.ensure_quota_limits()

        LOG.debug('Begin creating stack %r...', self.stack_name)
        try:
            created_id = self.client.stacks.create(
                stack_name=self.stack_name,
                template=self.template.template_yaml,
                parameters=parameters)['stack']['id']
        except exc.HTTPConflict:
            LOG.debug(f"Stack '{self.stack_name}' already created")
            return self.validate_created_stack()

        LOG.debug(f'New stack being created: name={self.stack_name}, '
                  f'id={created_id}.')
        invalid_id: typing.Optional[str] = created_id
        try:
            stack = self.validate_created_stack()
            if stack.id == created_id:
                LOG.debug('Stack successfully created "'
                          f"(name={self.stack_name}, id={created_id}).")
                invalid_id = None
            else:
                LOG.debug('Duplicate stack created "'
                          f"(name={self.stack_name}, id={created_id})...")
        finally:
            if invalid_id is not None:
                LOG.debug(f'Deleting invalid stack (name={self.stack_name}, "'
                          f'"id={invalid_id})...')
                self.delete_stack(stack_id=invalid_id)

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
        self.wait_until_stack_deleted()

    def delete_stack(self, stack_id=None):
        """Deletes stack."""
        self.stack = self._outputs = self._resources = None
        if not stack_id:
            stack_id = self.stack_id
        try:
            self.client.stacks.delete(stack_id)
        except exc.NotFound:
            LOG.debug('Stack already deleted: %r (id=%r)', self.stack_name,
                      stack_id)
        else:
            LOG.debug('Deleting stack %r (id=%r)...', self.stack_name,
                      stack_id)

    @property
    def stack_id(self) -> str:
        stack = self.stack
        if stack is None:
            return self.setup_stack_name()
        else:
            return stack.id

    def get_stack(self, resolve_outputs=False) \
            -> typing.Optional[stacks.Stack]:
        """Returns stack ID."""
        client = self.setup_client()
        try:
            self.stack = stack = client.stacks.get(
                self.stack_name, resolve_outputs=resolve_outputs)
        except exc.HTTPNotFound:
            LOG.debug(f"Stack '{self.stack_name}' not found")
            self.stack = stack = None
        finally:
            self._outputs = self._resources = None
        return stack

    def wait_for_create_complete(self,
                                 cached=True,
                                 check=True,
                                 timeout: tobiko.Seconds = None,
                                 interval: tobiko.Seconds = None) \
            -> typing.Optional[stacks.Stack]:
        return self.wait_for_stack_status(expected_status={CREATE_COMPLETE},
                                          cached=cached,
                                          check=check,
                                          timeout=timeout,
                                          interval=interval)

    def wait_for_delete_complete(self,
                                 check=True,
                                 cached=True,
                                 timeout: tobiko.Seconds = None,
                                 interval: tobiko.Seconds = None) \
            -> typing.Optional[stacks.Stack]:
        return self.wait_for_stack_status(expected_status={DELETE_COMPLETE},
                                          cached=cached,
                                          check=check,
                                          timeout=timeout,
                                          interval=interval)

    def wait_until_stack_deleted(self,
                                 check=True,
                                 cached=True,
                                 timeout: tobiko.Seconds = None,
                                 interval: tobiko.Seconds = None):
        # check stack has been completely deleted
        for attempt in tobiko.retry(timeout=timeout,
                                    interval=interval,
                                    default_timeout=self.wait_timeout,
                                    default_interval=self.wait_interval):
            # Ensure to refresh stack status
            stack = self.wait_for_delete_complete(check=check,
                                                  cached=cached,
                                                  timeout=attempt.time_left,
                                                  interval=attempt.interval)
            if stack is None:
                LOG.debug(f"Stack {self.stack_name} disappeared")
                break

            assert stack.stack_status == DELETE_COMPLETE
            if attempt.time_left == 0.:
                raise HeatStackDeletionFailed(
                    name=self.stack_name,
                    observed=stack.stack_status,
                    expected={DELETE_COMPLETE},
                    status_reason=stack.stack_status_reason)

            cached = False
            LOG.debug("Waiting for deleted stack to disappear: '%s'",
                      self.stack_name)
        else:
            raise RuntimeError("Retry look broken itself")

    def wait_for_stack_status(
            self,
            expected_status: typing.Container[str],
            check=True,
            cached=True,
            timeout: tobiko.Seconds = None,
            interval: tobiko.Seconds = None) \
            -> typing.Optional[stacks.Stack]:
        """Waits for the stack to reach the given status."""
        for attempt in tobiko.retry(
                timeout=timeout,
                interval=interval,
                default_timeout=self.wait_timeout,
                default_interval=self.wait_interval):
            if cached:
                cached = False
                stack = self.stack or self.get_stack()
            else:
                stack = self.get_stack()
            stack_status = getattr(stack, 'stack_status', DELETE_COMPLETE)
            if stack_status in expected_status:
                LOG.debug(f"Stack '{self.stack_name}' reached expected "
                          f"status: '{stack_status}'")
                break

            if not stack_status.endswith('_IN_PROGRESS'):
                LOG.warning(f"Stack '{self.stack_name}' reached unexpected "
                            f"status: '{stack_status}'")
                break

            if attempt.time_left == 0.:
                LOG.warning(f"Timed out waiting for stack '{self.stack_name}' "
                            f"status to change from '{stack_status}' to "
                            f"'{expected_status}'.")
                break

            LOG.debug(f"Waiting for stack '{self.stack_name}' status to "
                      f"change from '{stack_status}' to "
                      f"'{expected_status}'...")
        else:
            raise RuntimeError('Retry loop broken')

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

    def ensure_quota_limits(self):
        """Ensures quota limits before creating a new stack
        """
        self.ensure_neutron_quota_limits()
        self.ensure_nova_quota_limits()

    def ensure_neutron_quota_limits(self):
        required_quota_set = self.neutron_required_quota_set
        if required_quota_set:
            neutron.ensure_neutron_quota_limits(project=self.project,
                                                **required_quota_set)

    def ensure_nova_quota_limits(self):
        required_quota_set = self.nova_required_quota_set
        if required_quota_set:
            nova.ensure_nova_quota_limits(project=self.project,
                                          user=self.user,
                                          **required_quota_set)

    @property
    def neutron_required_quota_set(self) -> typing.Dict[str, int]:
        return collections.defaultdict(int)

    @property
    def nova_required_quota_set(self) -> typing.Dict[str, int]:
        return collections.defaultdict(int)


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
        if stack and not isinstance(stack, HeatStackFixture):
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


def check_stack_status(stack: stacks.Stack,
                       expected_status: typing.Container[str]):
    stack_status = stack.stack_status
    if stack_status in expected_status:
        return stack_status
    if stack_status == CREATE_FAILED and (
            CREATE_IN_PROGRESS in expected_status or
            CREATE_COMPLETE in expected_status):
        raise HeatStackCreationFailed(
            name=stack.name,
            observed=stack_status,
            expected=expected_status,
            status_reason=stack.stack_status_reason)
    if stack_status == DELETE_FAILED and (
            DELETE_IN_PROGRESS in expected_status or
            DELETE_COMPLETE in expected_status):
        raise HeatStackDeletionFailed(
            name=stack.stack_name,
            observed=stack_status,
            expected=expected_status,
            status_reason=stack.stack_status_reason)
    raise InvalidHeatStackStatus(
        name=stack.stack_name,
        observed=stack_status,
        expected=expected_status,
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


def random_sleep_time(min_time, max_time):
    assert min_time <= min_time
    return (max_time - min_time) * random.random() + min_time
