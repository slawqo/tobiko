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


NOT_CACHED = object()


class CachedProperty(object):
    """ Property that calls getter only the first time it is required

    It invokes property setter with the value returned by getter the first time
    it is required so that it is not requested again until del operator is not
    called again on top of target object.

    Implements default setter and deleter behaving as a regular attribute would
    by setting or removing named attribute of target object __dict__

    The name used for storing cached property value is got from getter function
    name if not passed as constructor attribute.

    Examples of use:

      class MyClass(object):

          @cached
          def my_property(self):
              return object()


      obj = MyClass()
      # my_property method not yet called
      assert 'my_property' not in obj.__dict__

      # my_property method is called
      first_value = obj.my_property
      assert obj.__dict__['my_property'] is first_value

      # my_property method is not called again
      assert obj.my_property is first_value

      # first value is removed from dictionary
      del obj.my_property
      assert 'my_property' not in obj.__dict__

      # my_property method is called
      second_value = obj.my_property
      assert obj.__dict__['my_property'] is second_value

      # value returned by second call of method can be different
      second_value is not first_value

    For more details about how Python properties works please refers to
    language documentation [1]

    [1] https://docs.python.org/3/howto/descriptor.html
    """

    fget = None
    fset = None
    fdel = None
    __doc__ = None
    cached_id = None

    def __init__(self, fget=None, fset=None, fdel=None, doc=None,
                 cached_id=None):
        if fget:
            self.getter(fget)
        if fset:
            self.setter(fset)
        if fdel:
            self.deleter(fdel)
        if doc:
            self.__doc__ = doc
        if cached_id:
            self.cached_id = cached_id
        elif self.cached_id is None:
            self.cached_id = '_cached_' + str(id(self))

    def getter(self, fget):
        assert callable(fget)
        self.fget = fget
        if self.__doc__ is None:
            self.__doc__ = fget.__doc__
        return fget

    def setter(self, fset):
        self.fset = fset
        return fset

    def deleter(self, fdel):
        self.fdel = fdel
        return fdel

    def __get__(self, obj, _objtype=None):
        if obj is None:
            return self

        value = self._get_cached(obj)
        if value is NOT_CACHED:
            if self.fget is None:
                raise AttributeError("Cached property has no getter method")
            value = self.fget(obj)
            self.__set__(obj, value)

        return value

    def __set__(self, obj, value):
        if self.fset:
            self.fset(obj, value)
        self._set_cached(obj, value)

    def __delete__(self, obj):
        if self.fdel:
            self.fdel(obj)
        self._delete_cached(obj)

    def _get_cached(self, obj):
        return getattr(obj, self.cached_id, NOT_CACHED)

    def _set_cached(self, obj, value):
        setattr(obj, self.cached_id, value)

    def _delete_cached(self, obj):
        return obj.__dict__.pop(self.cached_id, NOT_CACHED)


def cached(*args, **kwargs):
    return CachedProperty(*args, **kwargs)
