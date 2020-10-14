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

import typing  # noqa

from tobiko import _exception


T = typing.TypeVar('T')


class Selection(list, typing.Generic[T]):

    def with_attributes(self, **attributes):
        return self.create(
            filter_by_attributes(self, exclude=False, **attributes))

    def without_attributes(self, **attributes):
        return self.create(
            filter_by_attributes(self, exclude=True, **attributes))

    def with_items(self, **items):
        return self.create(filter_by_items(self, exclude=False, **items))

    def without_items(self, **items):
        return self.create(filter_by_items(self, exclude=True, **items))

    @classmethod
    def create(cls, objects: typing.Iterable[T]):
        return cls(objects)

    @property
    def first(self) -> T:
        if self:
            return self[0]
        else:
            raise ObjectNotFound()

    @property
    def unique(self) -> T:
        if len(self) > 1:
            raise MultipleObjectsFound(list(self))
        else:
            return self.first

    def __repr__(self):
        return '{!s}({!r})'.format(type(self).__name__, list(self))


def select(objects: typing.Iterable[T]) -> Selection[T]:
    return Selection.create(objects)


def filter_by_attributes(objects, exclude=False, **attributes):
    exclude = bool(exclude)
    for obj in objects:
        for key, value in attributes.items():
            matching = value == getattr(obj, key)
            if matching is exclude:
                break
        else:
            yield obj


def filter_by_items(dictionaries, exclude=False, **items):
    exclude = bool(exclude)
    for dictionary in dictionaries:
        for key, value in items.items():
            matching = value == dictionary[key]
            if matching is exclude:
                break
        else:
            yield dictionary


class ObjectNotFound(_exception.TobikoException):
    "Object not found"


class MultipleObjectsFound(_exception.TobikoException):
    "Multiple objects found: {objects!r}"
