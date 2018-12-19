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

import abc
import contextlib
import inspect

import six

import tobiko


def fixture(obj):
    obj.__tobiko_fixture__ = True
    return object


def is_fixture(obj):
    return getattr(obj, '__tobiko_fixture__', False)


def get_fixture(obj, manager=None):
    manager = manager or FIXTURES
    return manager.get_fixture(obj)


def create_fixture(obj, manager=None):
    manager = manager or FIXTURES
    return manager.create_fixture(obj)


def delete_fixture(obj, manager=None):
    manager = manager or FIXTURES
    return manager.delete_fixture(obj)


def get_required_fixtures(obj, manager=None):
    manager = manager or FIXTURES
    return manager.get_required_fixtures(obj)


def discover_required_fixtures(objects, manager=None):
    manager = manager or FIXTURES
    return sorted(set(manager.discover_required_fixtures(objects, manager)))


def create_fixtures(objects, manager=None):
    manager = manager or FIXTURES
    for _fixture in discover_required_fixtures(objects=objects,
                                              manager=manager):
        manager.create_fixture(_fixture)


def delete_fixtures(objects, manager=None):
    manager = manager or FIXTURES
    for _fixture in discover_required_fixtures(objects=objects,
                                              manager=manager):
        return manager.delete_fixture(_fixture)


class FixtureManager(object):

    def __init__(self):
        self.fixtures = {}

    def get_fixture(self, obj):
        name = get_object_name(obj)
        _fixture = self.fixtures.get(name)
        if _fixture is None:
            _fixture = self.init_fixture(name=name, obj=obj)
            assert isinstance(_fixture, Fixture)
            self.fixtures[name] = _fixture
        return _fixture

    def create_fixture(self, obj):
        return self.get_fixture(obj).create_fixture()

    def delete_fixture(self, obj):
        return self.get_fixture(obj).delete_fixture()

    def init_fixture(self, obj, name):
        if isinstance(obj, six.string_types):
            if name != obj:
                msg = ("Fixture name mismatch: "
                       "{!r} != {!r}").format(name, obj.fixture_name)
                raise ValueError(msg)
            obj = tobiko.load_object(name)

        if isinstance(obj, Fixture):
            if name != obj.fixture_name:
                msg = ("Fixture name mismatch: "
                       "{!r} != {!r}").format(name, obj.fixture_name)
                raise ValueError(msg)
            return obj
        elif inspect.isclass(obj):
            if issubclass(obj, Fixture):
                return obj(fixture_name=name)
        elif inspect.isgeneratorfunction(obj):
            return ContextFixture(
                fixture_name=name, context=contextlib.contextmanager(obj))
        elif inspect.isfunction(obj):
            return FunctionFixture(fixture_name=name, function=obj)
        raise TypeError("Invalid fixture object type: {!r}".format(object))

    def get_required_fixtures(self, obj):
        return sorted(set(self.discover_required_fixtures([obj])))

    def discover_required_fixtures(self, objects):
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


FIXTURES = FixtureManager()


class Fixture(object):

    __tobiko_fixture__ = True

    def __init__(self, fixture_name):
        self.fixture_name = fixture_name

    @abc.abstractmethod
    def create_fixture(self):
        pass

    def delete_fixture(self):
        pass


class FunctionFixture(Fixture):

    def __init__(self, fixture_name, function):
        super(FunctionFixture, self).__init__(fixture_name=fixture_name)
        assert callable(function)
        self.function = function

    def create_fixture(self):
        return self.function()


class ContextFixture(Fixture):

    def __init__(self, fixture_name, context):
        super(ContextFixture, self).__init__(fixture_name=fixture_name)
        self.context = context

    def create_fixture(self):
        return self.context.__enter__()

    def delete_fixture(self):
        return self.context.__exit__(None, None, None)


def get_object_name(obj):
    if isinstance(obj, six.string_types):
        return obj

    if is_fixture(obj):
        name = getattr(obj, 'fixture_name', None)
        if name:
            return name

    name = getattr(obj, '__qualname__', None)
    if name:
        return obj.__module__ + '.' + name

    module = inspect.getmodule(obj).__name__
    if inspect.isclass(obj):
        return module + '.' + obj.__name__

    parent_class = getattr(obj, 'im_class', None)
    if parent_class:
        return module + parent_class.__name__ + '.' + obj.__name__

    if inspect.isfunction(obj):
        return module + '.' + obj.func_name

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
