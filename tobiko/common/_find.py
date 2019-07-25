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


def find_by_attributes(objects, exclude=False, **attributes):
    exclude = bool(exclude)
    if attributes:
        selection = []
        for obj in objects:
            for key, value in attributes.items():
                matching = value == getattr(obj, key)
                if matching is exclude:
                    break
            else:
                selection.append(obj)
        objects = selection
    return objects


def find_by_items(mappings, exclude=False, **items):
    exclude = bool(exclude)
    if items:
        selection = []
        for mapping in mappings:
            for key, value in items.items():
                matching = value == mapping[key]
                if matching is exclude:
                    break
            else:
                selection.append(mapping)
        mappings = selection
    return mappings
