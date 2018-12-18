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
import inspect

import six


def get_fixture_name(obj):
    if isinstance(obj, six.string_types):
        return obj

    elif (isinstance(obj, six.class_types) and
          issubclass(obj, Fixture)):
        return obj.fixture_name

    msg = "{!r} is not a string type or a subclass of {!s}".format(
        obj, Fixture)
    raise TypeError(msg)


class FixtureManager(object):

    def __init__(self):
        self.fixtures = {}

    def set(self, name, cls):
        if not issubclass(cls, Fixture):
            msg = "{!r} is not a subclass of {!s}".format(cls, Fixture)
            raise TypeError(msg)
        fixture = cls()
        actual_fixture = self.fixtures.setdefault(name, fixture)
        if actual_fixture is not fixture:
            msg = "Fixture with named {!r} already registered: {!r}".format(
                name, actual_fixture)
            raise ValueError(msg)
        return fixture

    def get(self, cls_or_name):
        name = get_fixture_name(cls_or_name)
        fixture = self.fixtures.get(name)
        if fixture is None:
            raise ValueError('Invalid fixture name: {!r}'.format(name))
        return fixture

    def create(self, cls_or_name):
        fixture = self.get(cls_or_name)
        fixture.create_fixture()
        return fixture

    def delete(self, cls_or_name):
        fixture = self.get(cls_or_name)
        fixture.delete_fixture()
        return fixture


FIXTURES = FixtureManager()


class FixtureMeta(abc.ABCMeta):

    def __new__(cls, name, bases, members):
        fixture_class = super(FixtureMeta, cls).__new__(cls, name, bases,
                                                        members)
        if not inspect.isabstract(fixture_class):
            fixture_name = getattr(fixture_class, 'fixture_name', None)
            if fixture_name is None:
                fixture_class.fixture_name = fixture_name = (
                    fixture_class.__module__ + '.' +
                    fixture_class.__name__)
                FIXTURES.set(fixture_name, fixture_class)
        return fixture_class


@six.add_metaclass(FixtureMeta)
class Fixture(object):

    @abc.abstractmethod
    def create_fixture(self):
        pass

    def delete_fixture(self):
        pass
