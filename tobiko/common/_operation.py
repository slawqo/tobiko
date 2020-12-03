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

import inspect

from oslo_log import log
import testtools

from tobiko.common import _exception
from tobiko.common import _fixture
from tobiko.common import _skip


LOG = log.getLogger(__name__)


def runs_operation(operation_object):
    return RunsOperationProperty(operation_object)


class RunsOperations(object):

    def setUp(self):
        super(RunsOperations, self).setUp()  # pylint: disable=no-member
        for operation_name in get_runs_operation_names(self):
            get_operation(operation_name)


def add_runs_operation_name(obj, name):
    required_names = getattr(obj, '__tobiko_runs_operations__', None)
    if not isinstance(required_names, set):
        if required_names:
            required_names = set(required_names)
        else:
            required_names = set()
        # cache list for later use
        obj.__tobiko_runs_operations__ = required_names
    required_names.add(name)


def get_runs_operation_names(obj):
    '''Get operation names required by given :param obj:'''

    name, obj = _fixture.get_name_and_object(obj)

    operations = getattr(obj, '__tobiko_runs_operations__', set())
    if isinstance(operations, tuple):
        return operations

    try:
        # froze required names to avoid re-discovering them again
        obj.__tobiko_runs_operations__ = tuple()
    except AttributeError:
        # ignore this object because not defined by Python code
        return tuple()

    LOG.debug('Discover operations for object %r', name)
    if operations:
        operations = set(operations)

    if inspect.ismethod(obj) or inspect.isfunction(obj):
        pass  # decorated functions have __tobiko_runs_operations__ defined

    else:
        if not inspect.isclass(obj):
            obj = type(obj)
        operations.update(get_runs_operation_names_from_class(obj))

    # Return every operation in alphabetical order and
    # froze required names to avoid re-discovering them again
    operations = tuple(sorted(operations))
    obj.__tobiko_runs_operations__ = operations
    return operations


def get_runs_operation_names_from_class(cls):
    """Get list of members of type RequiredFixtureProperty of given class"""

    # inspect.getmembers() would iterate over such many testtools.TestCase
    # members too, so let exclude members from those very common base classes
    # that we know doesn't have members of type RunsOperationProperty
    base_classes = cls.__mro__
    for base_class in [testtools.TestCase, _fixture.SharedFixture]:
        if issubclass(cls, base_class):
            base_classes = base_classes[:base_classes.index(base_class)]
            break

    # Get all members for selected class without calling properties or methods
    members = {}
    for base_class in reversed(base_classes):
        members.update(base_class.__dict__)

    # Return all member operation names
    operations = set()
    for name, member in sorted(members.items()):
        if not name.startswith('__'):
            operations.update(get_runs_operation_names(obj=member))
    return operations


class RunsOperationProperty(object):

    def __init__(self, obj):
        self.name, self.obj = _fixture.get_name_and_object(obj)

    @property
    def __tobiko_runs_operations__(self):
        return (self.name,)

    def before_operation(self, obj):

        def is_before():
            return self.get_operation().is_before

        decorator = _skip.skip_unless(f"Before operation {self.name}",
                                      is_before)

        return self.with_operation(decorator(obj))

    def after_operation(self, obj):

        def is_after():
            return self.get_operation().is_after

        decorator = _skip.skip_unless(f"After operation {self.name}",
                                      is_after)

        return self.with_operation(decorator(obj))

    def with_operation(self, obj):
        add_runs_operation_name(obj, self.name)
        return obj

    def __get__(self, instance, _):
        if instance is None:
            return self
        else:
            return self.get_operation()

    def get_operation(self):
        return get_operation(self.obj)


def before_operation(obj):
    return RunsOperationProperty(obj).before_operation


def after_operation(obj):
    return RunsOperationProperty(obj).after_operation


def with_operation(obj):
    return RunsOperationProperty(obj).with_operation


def get_operation(obj):
    operation = _fixture.get_fixture(obj)
    _exception.check_valid_type(operation, Operation)

    if operation.is_before and operation_config().run_operations:
        operation = _fixture.setup_fixture(obj)

    return operation


def get_operation_name(obj):
    return _fixture.get_object_name(obj)


def operation_config():
    return _fixture.setup_fixture(OperationsConfigFixture)


class OperationsConfigFixture(_fixture.SharedFixture):

    after_operations = None
    run_operations = None

    def setup_fixture(self):
        from tobiko import config
        self.after_operations = set(
            config.get_list_env('TOBIKO_AFTER_OPERATIONS'))
        self.run_operations = config.get_bool_env(
            'TOBIKO_RUN_OPERATIONS') or False


class Operation(_fixture.SharedFixture):

    @property
    def operation_name(self):
        return _fixture.get_fixture_name(self)

    @property
    def is_before(self):
        return not self.is_after

    _is_after = None

    @property
    def is_after(self):
        is_after = self._is_after
        if is_after is None:
            config = operation_config()
            is_after = self.operation_name in config.after_operations
            self._is_after = is_after
        return is_after

    def setup_fixture(self):
        if not self.is_after:
            LOG.debug('Executing operation: %r', self.operation_name)
            try:
                self.run_operation()
            except Exception as ex:
                LOG.debug('Operation %r failed: %r', self.operation_name, ex)
                raise
            else:
                LOG.debug('Operation executed: %r', self.operation_name)
            finally:
                self._is_after = True

    def run_operation(self):
        raise NotImplementedError
