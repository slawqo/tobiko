# Copyright (c) 2021 Red Hat
# All Rights Reserved.
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
import re
import typing

import tobiko
from tobiko.tests import unit


def condition(value):
    return value


class Obj(typing.NamedTuple):
    number: int = 0
    text: str = ''


T = typing.TypeVar('T')


class SelectionTest(unit.TobikoUnitTest):

    @staticmethod
    def create_selection(*args, **kwargs):
        return tobiko.Selection(*args, **kwargs)

    def test_selection(self,
                       objects: typing.Iterable[T] = tuple()) \
            -> tobiko.Selection[T]:
        reference = list(objects)
        if isinstance(objects, collections.Generator):
            # Can't reiterate the same generator twice
            objects = (o for o in reference)
            assert isinstance(objects, collections.Generator)
        elif isinstance(objects, collections.Iterator):
            # Can't reiterate the same iterator twice
            objects = iter(reference)
            assert isinstance(objects, collections.Iterator)

        selection = self.create_selection(objects)
        self.assertIsInstance(selection, list)
        self.assertIsInstance(selection, tobiko.Selection)
        self.assertEqual(reference, selection)
        self.assertEqual(selection, reference)
        return selection

    def test_selection_with_list(self):
        self.test_selection([1, 'a', 3.14])

    def test_selection_with_tuple(self):
        self.test_selection((1, 'a', 3.14))

    def test_selection_with_generator(self):
        self.test_selection(c for c in 'hello')

    def test_selection_with_iterator(self):
        self.test_selection(iter('hello'))

    def test_with_attribute(self):
        a = Obj(0, 'a')
        b = Obj(1, 'b')
        c = Obj(1, 'c')
        selection = self.create_selection([a, b, c])
        self.assertEqual([a], selection.with_attributes(text='a'))
        self.assertEqual([b], selection.with_attributes(text='b'))
        self.assertEqual([c], selection.with_attributes(text='c'))
        self.assertEqual([a], selection.with_attributes(number=0))
        self.assertEqual([b, c], selection.with_attributes(number=1))
        self.assertEqual([], selection.with_attributes(number=2))
        self.assertEqual([b], selection.with_attributes(number=1, text='b'))
        self.assertEqual([], selection.with_attributes(number=1, text='a'))
        self.assertEqual([a, b],
                         selection.with_attributes(text=re.compile('(a|b)')))

    def test_without_attribute(self):
        a = Obj(0, 'a')
        b = Obj(1, 'b')
        c = Obj(1, 'c')
        selection = self.create_selection([a, b, c])
        self.assertEqual([b, c], selection.without_attributes(text='a'))
        self.assertEqual([a, c], selection.without_attributes(text='b'))
        self.assertEqual([a, b], selection.without_attributes(text='c'))
        self.assertEqual([b, c], selection.without_attributes(number=0))
        self.assertEqual([a], selection.without_attributes(number=1))
        self.assertEqual([a, b, c], selection.without_attributes(number=2))
        self.assertEqual([a], selection.without_attributes(number=1, text='b'))
        self.assertEqual([], selection.without_attributes(number=1, text='a'))
        self.assertEqual([c],
                         selection.without_attributes(
                             text=re.compile('(a|b)')))

    def test_with_items(self):
        a = {'number': 0, 'text': 'a'}
        b = {'number': 1, 'text': 'b'}
        c = {'number': 1, 'text': 'c'}
        selection = self.create_selection([a, b, c])
        self.assertEqual([a], selection.with_items(text='a'))
        self.assertEqual([b], selection.with_items(text='b'))
        self.assertEqual([c], selection.with_items(text='c'))
        self.assertEqual([a], selection.with_items(number=0))
        self.assertEqual([b, c], selection.with_items(number=1))
        self.assertEqual([], selection.with_items(number=2))
        self.assertEqual([b], selection.with_items(number=1, text='b'))
        self.assertEqual([], selection.with_items(number=1, text='a'))
        self.assertEqual([a, b],
                         selection.with_items(text=re.compile('(a|b)')))

    def test_without_items(self):
        a = {'number': 0, 'text': 'a'}
        b = {'number': 1, 'text': 'b'}
        c = {'number': 1, 'text': 'c'}
        selection = self.create_selection([a, b, c])
        self.assertEqual([b, c], selection.without_items(text='a'))
        self.assertEqual([a, c], selection.without_items(text='b'))
        self.assertEqual([a, b], selection.without_items(text='c'))
        self.assertEqual([b, c], selection.without_items(number=0))
        self.assertEqual([a], selection.without_items(number=1))
        self.assertEqual([a, b, c], selection.without_items(number=2))
        self.assertEqual([a], selection.without_items(number=1, text='b'))
        self.assertEqual([], selection.without_items(number=1, text='a'))
        self.assertEqual([c],
                         selection.without_items(text=re.compile('(a|b)')))

    def test_select(self):
        a = Obj(0, 'a')
        b = Obj(1, 'b')
        c = Obj(1, 'c')
        selection = self.create_selection([a, b, c])
        self.assertEqual([b, c], selection.select(lambda obj: obj.number == 1))

    def test_unselect(self):
        a = Obj(0, 'a')
        b = Obj(1, 'b')
        c = Obj(1, 'c')
        selection = self.create_selection([a, b, c])
        self.assertEqual([a], selection.unselect(lambda obj: obj.number == 1))


class SelectTest(SelectionTest):

    @staticmethod
    def create_selection(*args, **kwargs):
        return tobiko.select(*args, **kwargs)
