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

import importlib
import inspect
import weakref
import sys


_REF_TO_NONE = object()


def load_object(object_id, manager=None, new_loader=None, cached=True):
    manager = manager or LOADERS
    loader = manager.get_loader(object_id=object_id, new_loader=new_loader)
    return loader.load(manager=manager, cached=cached)


class ObjectLoader(object):
    """Previously loaded object meta-data"""

    # Weak reference to target object
    _ref = None

    # Flag that tells if referenced object is an imported module
    _is_module = None

    def __init__(self, object_id):
        # Object ID
        self._id = object_id
        if '.' in object_id:
            # Extract object name and parent id from object id
            parent_id, name = object_id.rsplit('.', 1)
            self._name = name
            self._parent_id = parent_id
        else:
            # Root objects have no parent
            self._name = object_id
            self._parent_id = None

    @property
    def is_module(self):
        return self._is_module

    @property
    def id(self):
        return self._id

    def __repr__(self):
        return '{cls!s}({id!r})'.format(cls=type(self).__name__, id=self._id)

    def get(self):
        if self._is_module:
            return sys.modules.get(self._id)

        ref = self._ref
        if ref is _REF_TO_NONE:
            return None

        if callable(ref):
            obj = ref()
            if obj is not None:
                return obj

        msg = "Object {!r} not cached".format(self._id)
        raise RuntimeError(msg)

    def load(self, manager, cached=True):
        if cached:
            try:
                return self.get()
            except RuntimeError:
                pass

        obj = None
        parent_id = self._parent_id
        if parent_id:
            parent_loader = manager.get_loader(object_id=parent_id,
                                               new_loader=type(self))
            parent = parent_loader.load(manager=manager, cached=cached)
            name = self._name
            try:
                obj = getattr(parent, name)
            except AttributeError:
                if not parent_loader.is_module:
                    # Child cannot be a module if parent isn't a module
                    raise
            else:
                if obj is None:
                    # Cannot create weak reference to None
                    self._ref = _REF_TO_NONE
                elif inspect.ismodule(obj):
                    # Cannot create weak reference to Module
                    self._is_module = True
                else:
                    self._ref = weakref.ref(obj)
                return obj

        if obj is None:
            obj = importlib.import_module(self._id)
            self._is_module = True
        return obj


class LoaderManager(object):

    def __init__(self):
        # Dictionary used to cache object references
        self._loaders = {}

    new_loader = ObjectLoader

    def get_loader(self, object_id, new_loader=None):
        """Get existing ObjectInfo or create new one

        It implements singleton pattern by caching previously created
        ObjectInfo instances to OBJECT_INFOS for later retrieval
        """
        try:
            return self._loaders[object_id]
        except KeyError:
            pass

        new_loader = new_loader or self.new_loader
        loader = new_loader(object_id=object_id)
        if not isinstance(loader, ObjectLoader):
            msg = "{!r} is not instance of class ObjectLoader".format(
                loader)
            raise TypeError(msg)

        self._loaders[object_id] = loader
        return loader


LOADERS = LoaderManager()
