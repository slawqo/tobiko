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

import re
import typing

from tobiko import _exception


T = typing.TypeVar('T')


class Selection(list, typing.Generic[T]):

    def with_attributes(self, **attributes) -> 'Selection[T]':
        return self.select(lambda obj: equal_attributes(obj, attributes))

    def without_attributes(self, **attributes) -> 'Selection[T]':
        return self.select(lambda obj: equal_attributes(obj, attributes,
                                                        inverse=True))

    def with_items(self: 'Selection[typing.Dict]', **items) \
            -> 'Selection[typing.Dict]':
        return self.select(lambda obj: equal_items(obj, items))

    def without_items(self: 'Selection[typing.Dict]', **items) -> \
            'Selection[typing.Dict]':
        return self.select(lambda obj: equal_items(obj, items, inverse=True))

    @classmethod
    def create(cls, objects: typing.Iterable[T]) -> 'Selection[T]':
        return cls(objects)

    def select(self,
               predicate: typing.Callable[[T], bool],
               expect=True) \
            -> 'Selection[T]':
        return self.create(obj
                           for obj in self
                           if bool(predicate(obj)) is expect)

    def unselect(self,
                 predicate: typing.Callable[[T], typing.Any]) \
            -> 'Selection[T]':
        return self.select(predicate, expect=False)

    @property
    def first(self) -> T:
        if self:
            return self[0]
        else:
            raise ObjectNotFound()

    @property
    def last(self) -> T:
        if self:
            return self[-1]
        else:
            raise ObjectNotFound()

    @property
    def unique(self) -> T:
        if len(self) > 1:
            raise MultipleObjectsFound(list(self))
        else:
            return self.first

    def __repr__(self):
        return f'{type(self).__name__}({list(self)!r})'


def select(objects: typing.Iterable[T]) -> Selection[T]:
    return Selection.create(objects)


def equal_attributes(obj,
                     attributes: typing.Dict[str, typing.Any],
                     inverse=False) \
        -> bool:
    for key, matcher in attributes.items():
        matching = match(matcher, getattr(obj, key))
        if matching is inverse:
            return False
    return True


def equal_items(obj: typing.Dict,
                items: typing.Dict,
                inverse=False) -> bool:
    for key, matcher in items.items():
        matching = match(matcher, obj[key])
        if matching is inverse:
            return False
    return True


PatternType = type(re.compile("", 0))


def match(matcher: typing.Any, value: typing.Any) -> bool:
    if isinstance(matcher, PatternType):
        return matcher.match(value) is not None
    else:
        return matcher == value


class ObjectNotFound(_exception.TobikoException):
    message = "Object not found"


class MultipleObjectsFound(_exception.TobikoException):
    message = "Multiple objects found: {objects!r}"
