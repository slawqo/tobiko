# Copyright 2020 Red Hat
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

import tobiko
from tobiko.tests import unit


NOT_CALLED = object()


class TestCached(unit.TobikoUnitTest):

    my_property = tobiko.cached(doc='some doc')

    def test_init(self):
        prop = type(self).my_property
        self.assertIsNone(prop.fget)
        self.assertIsNone(prop.fset)
        self.assertIsNone(prop.fdel)
        self.assertEqual('some doc', prop.__doc__)
        self.assertTrue(prop.cached_id)

    def test_get(self):
        ex = self.assertRaises(AttributeError, lambda: self.my_property)
        self.assertEqual("Cached property has no getter method", str(ex))

    def test_set(self):
        self.my_property = value = object()
        self.assertIs(value, self.my_property)

    def test_delete(self):
        self.my_property = object()
        del self.my_property
        ex = self.assertRaises(AttributeError, lambda: self.my_property)
        self.assertEqual("Cached property has no getter method", str(ex))


class TestCachedWithGetter(unit.TobikoUnitTest):

    @tobiko.cached
    def my_property(self):
        return object()

    def test_init(self):
        # pylint: disable=no-member
        prop = type(self).my_property
        assert isinstance(prop, tobiko.CachedProperty)
        self.assertTrue(callable(prop.fget))
        self.assertIsNone(prop.fset)
        self.assertIsNone(prop.fdel)
        self.assertIs(prop.fget.__doc__, prop.__doc__)
        self.assertTrue(prop.cached_id)

    def test_get(self):
        value = self.my_property
        self.assertIs(value, self.my_property)

    def test_set(self):
        self.my_property = value = object()
        self.assertIs(value, self.my_property)

    def test_delete(self):
        self.my_property = value = object()
        del self.my_property
        self.assertIsNot(value, self.my_property)


class TestCachedWithSetter(unit.TobikoUnitTest):

    _set_value = None

    def set_my_property(self, value):
        self._set_value = value

    my_property = tobiko.cached(fset=set_my_property)

    def test_init(self):
        prop = type(self).my_property
        self.assertIsNone(prop.fget)
        self.assertIs(type(self).set_my_property, prop.fset)
        self.assertIsNone(prop.fdel)
        self.assertIsNone(prop.__doc__)
        self.assertTrue(prop.cached_id)

    def test_get(self):
        self.assertFalse(hasattr(self, 'my_property'))
        self.assertIsNone(self._set_value)

    def test_set(self):
        self.my_property = value = object()
        self.assertIs(value, self.my_property)
        self.assertIs(value, self._set_value)

    def test_delete(self):
        self.my_property = object()
        del self.my_property
        self.assertFalse(hasattr(self, 'my_property'))


class TestCachedWithDeleter(unit.TobikoUnitTest):

    _delete_value = None

    def delete_my_property(self):
        self._delete_value = object()

    my_property = tobiko.cached(fdel=delete_my_property)

    def test_init(self):
        prop = type(self).my_property
        self.assertIsNone(prop.fget)
        self.assertIsNone(prop.fset)
        self.assertIs(type(self).delete_my_property, prop.fdel)
        self.assertIsNone(prop.__doc__)
        self.assertTrue(prop.cached_id)

    def test_get(self):
        self.assertFalse(hasattr(self, 'my_property'))
        self.assertIsNone(self._delete_value)

    def test_set(self):
        self.my_property = value = object()
        self.assertIs(value, self.my_property)
        self.assertIsNone(self._delete_value)

    def test_delete(self):
        self.my_property = object()
        del self.my_property
        self.assertFalse(hasattr(self, 'my_property'))
        self.assertIsNotNone(self._delete_value)


class TestCachedWithDoc(unit.TobikoUnitTest):

    my_doc = 'some doc'

    my_property = tobiko.cached(doc=my_doc)

    @my_property.getter
    def get_my_property(self):
        return object()

    def test_init(self):
        prop = type(self).my_property
        self.assertTrue(callable(prop.fget))
        self.assertIsNone(prop.fset)
        self.assertIsNone(prop.fdel)
        self.assertIs(self.my_doc, prop.__doc__)
        self.assertTrue(prop.cached_id)


class TestCachedWithCachedId(unit.TobikoUnitTest):

    cached_id = 'my_cached_id'

    my_property = tobiko.cached(cached_id=cached_id)

    @my_property.getter
    def get_my_property(self):
        return object()

    def test_init(self):
        prop = type(self).my_property
        self.assertTrue(callable(prop.fget))
        self.assertIsNone(prop.fset)
        self.assertIsNone(prop.fdel)
        self.assertIsNone(prop.__doc__)
        self.assertEqual(self.cached_id, prop.cached_id)
        self.assertFalse(hasattr(self, 'my_cached_id'))

    def test_get(self):
        # pylint: disable=no-member
        value = self.my_property
        self.assertIs(value, self.my_property)
        self.assertIs(value, self.my_cached_id)

    def test_set(self):
        # pylint: disable=no-member
        self.my_property = value = object()
        self.assertIs(value, self.my_property)
        self.assertIs(value, self.my_cached_id)

    def test_delete(self):
        # pylint: disable=no-member
        self.my_property = value = object()
        del self.my_property
        self.assertIsNot(value, self.my_property)
        self.assertIsNot(value, self.my_cached_id)


class TestCachedWithDecorators(unit.TobikoUnitTest):

    my_property = tobiko.cached()

    getter_called = 0

    @my_property.getter
    def getter(self):
        """Getter documentation"""
        self.getter_called += 1
        return object()

    setter_called = tuple()  # type: typing.Tuple

    @my_property.setter
    def setter(self, value):
        self.setter_called += (value,)

    deleter_called = 0

    @my_property.deleter
    def deleter(self):
        self.deleter_called += 1

    def test_init(self):
        # self.my_property method not called yet
        prop = type(self).my_property
        self.assertIs(type(self).getter, prop.fget)
        self.assertIs(type(self).setter, prop.fset)
        self.assertIs(type(self).deleter, prop.fdel)
        self.assertIs(self.getter.__doc__, prop.__doc__)
        self.assertTrue(prop.cached_id)

    def test_get(self):
        # my_property method is called
        prop = type(self).my_property
        value = self.my_property
        self.assertEqual(1, self.getter_called)
        self.assertIs(value, getattr(self, prop.cached_id))
        self.assertEqual((value,), self.setter_called)
        return value

    def test_get_twice(self):
        # my_property method is not called again
        value1 = self.test_get()
        value2 = self.test_get()
        self.assertIs(value1, value2)

    def test_set(self):
        # property value is stored into the object
        prop = type(self).my_property
        self.my_property = value = object()
        self.assertIs(value, self.my_property)
        self.assertEqual(0, self.getter_called)
        self.assertEqual(value, self.setter_called[-1])
        self.assertIs(value, getattr(self, prop.cached_id))
        return value

    def test_set_twice(self):
        # stored value is got after setting
        value1 = self.test_set()
        value2 = self.test_set()
        self.assertIsNot(value1, value2)

    def test_delete(self):
        # deleting remove stored value
        prop = type(self).my_property
        value = self.test_set()
        del self.my_property
        self.assertFalse(hasattr(self, prop.cached_id))
        self.assertIsNot(value, self.my_property)
        self.assertEqual(1, self.deleter_called)
