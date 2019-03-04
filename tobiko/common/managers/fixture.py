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

import inspect

import fixtures
import six

import tobiko


def is_fixture(obj):
    return (getattr(obj, '__tobiko_fixture__', False) or
            isinstance(obj, fixtures.Fixture) or
            (inspect.isclass(obj) and issubclass(obj, fixtures.Fixture)))


def get_fixture(obj, manager=None):
    manager = manager or FIXTURES
    return manager.get_fixture(obj)


def get_fixture_name(obj):
    return get_fixture(obj).__tobiko_fixture_name__


def remove_fixture(obj, manager=None):
    manager = manager or FIXTURES
    return manager.remove_fixture(obj)


def setup_fixture(obj, manager=None):
    fixture = get_fixture(obj, manager=manager)
    fixture.setUp()
    return fixture


def setup_shared_fixture(obj, manager=None):
    fixture = get_fixture(obj, manager=manager)
    fixture.setup_shared_fixture()
    return fixture


def cleanup_fixture(obj, manager=None):
    fixture = get_fixture(obj, manager=manager)
    fixture.cleanUp()
    return fixture


def cleanup_shared_fixture(obj, manager=None):
    fixture = get_fixture(obj, manager=manager)
    fixture.cleanup_shared_fixture()
    return fixture


def iter_required_fixtures(objects):
    objects = list(objects)
    while objects:
        obj = objects.pop()
        if isinstance(obj, six.string_types):
            object_id = obj
            obj = tobiko.load_object(object_id)
        else:
            object_id = get_object_name(obj)

        if is_fixture(obj):
            yield object_id

        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            for default in get_default_param_values(obj):
                if is_fixture(default):
                    yield get_object_name(default)

        if inspect.ismodule(obj):
            members = [obj for _, obj in inspect.getmembers(obj)
                       if (inspect.isfunction(obj) or
                           inspect.isclass(obj))]
            objects.extend(members)

        elif inspect.isclass(obj):
            members = [obj for _, obj in inspect.getmembers(obj)
                       if (inspect.isfunction(obj) or
                           inspect.ismethod(obj))]
            objects.extend(members)


def list_required_fixtures(objects):
    return sorted(set(iter_required_fixtures(objects)))


def setup_required_fixtures(objects, manager=None):
    for name in iter_required_fixtures(objects=objects):
        yield setup_fixture(name, manager=manager)


def cleanup_required_fixtures(objects, manager=None):
    manager = manager or FIXTURES
    for name in iter_required_fixtures(objects=objects):
        yield cleanup_fixture(name, manager=manager)


def init_fixture(obj, name):
    if isinstance(obj, six.string_types):
        obj = tobiko.load_object(name)

    if (inspect.isclass(obj) and issubclass(obj, fixtures.Fixture)):
        obj = obj()

    if isinstance(obj, fixtures.Fixture):
        obj.__tobiko_fixture__ = True
        obj.__tobiko_fixture_name__ = name
        return obj

    raise TypeError("Invalid fixture object type: {!r}".format(object))


def get_object_name(obj):
    if isinstance(obj, six.string_types):
        return obj

    name = getattr(obj, '__tobiko_fixture_name__', None)
    if name:
        return name

    module = inspect.getmodule(obj).__name__

    if six.PY2:
        # Below code is only for old Python versions
        if inspect.isclass(obj):
            # This doesn't work for nested classes
            return module + '.' + obj.__name__

        method_class = getattr(obj, 'im_class', None)
        if method_class:
            # This doesn't work for nested classes
            return module + method_class.__name__ + '.' + obj.__name__

        if inspect.isfunction(obj):
            return module + '.' + obj.func_name

    else:
        # Only Python 3 defines __qualname__
        name = getattr(obj, '__qualname__', None)
        if name:
            return module + '.' + name

    msg = "Unable to get fixture name from object {!r}".format(obj)
    raise TypeError(msg)


def get_default_param_values(obj):
    if hasattr(inspect, 'signature'):
        try:
            signature = inspect.signature(obj)
        except ValueError:
            pass
        else:
            return [param.default
                    for param in signature.parameters.values()]

    # Use old deprecated function 'getargspec'
    return list(inspect.getargspec(obj).defaults or  # pylint: disable=W1505
                tuple())


class FixtureManager(object):

    def __init__(self):
        self.fixtures = {}

    def get_fixture(self, obj, init=init_fixture):
        name = get_object_name(obj)
        fixture = self.fixtures.get(name)
        if fixture is None:
            self.fixtures[name] = fixture = init(name=name, obj=obj)
            assert isinstance(fixture, fixtures.Fixture)
        return fixture

    def remove_fixture(self, obj):
        name = get_object_name(obj)
        return self.fixtures.pop(name, None)


FIXTURES = FixtureManager()


class SharedFixture(fixtures.Fixture):
    """Base class for fixtures intended to be shared between multiple tests

    Make sure that fixture setUp method can be called more than once, but
    actually executing _setUp method only the first time. This allows the
    fixture to be passed to useFixture methods multiple times without caring
    about if has already been used before.

    Fixture set up can anyway be forced by calling 'setup_shared_fixture'
    method.

    Because cleanup policy in a shared fixture is different from a common
    fixture, cleanUp method simply doesn't nothing.

    Actual fixture cleanup is executed by calling
    cleanup_shared_fixture method.

    """

    _setup_executed = False

    def __init__(self):
        self._clear_cleanups()

    def setUp(self):
        """Executes _setUp method only the first time setUp is called"""
        if not self._setup_executed:
            self.setup_shared_fixture()

    def setup_shared_fixture(self):
        """Forces execution of _setUp method"""
        super(SharedFixture, self).setUp()
        self._setup_executed = True

    def cleanUp(self, raise_first=True):
        """Id doesn't nothing"""

    def cleanup_shared_fixture(self, raise_first=True):
        """Executes registered cleanups"""
        super(SharedFixture, self).cleanUp(raise_first)
        self._setup_executed = False
