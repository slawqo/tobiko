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

import tobiko


class ResourceNotFound(tobiko.TobikoException):
    message = ("No such resource found for obj={obj!r} and "
               "properties={properties!r}")


class MultipleResourcesFound(tobiko.TobikoException):
    message = ("{count} resources found for obj={obj!r} and "
               "properties={properties!r}: {resource_ids}")


def find_resource(obj, resources, properties=None, check_found=True,
                  check_unique=True):
    properties = properties and list(properties) or ['id', 'name']
    resources_it = find_resources(obj=obj,
                                  resources=resources,
                                  properties=properties)
    try:
        resource = next(resources_it)

    except StopIteration:
        # Resource not found
        if check_found:
            raise ResourceNotFound(obj=obj, properties=properties)
        else:
            return None

    else:
        # Resource found
        if check_unique:
            duplicates = [r['id'] for r in resources_it]
            if duplicates:
                resources_ids = [resource['id']] + duplicates
                count = 1 + len(duplicates)
                raise MultipleResourcesFound(obj=obj,
                                             properties=properties,
                                             count=count,
                                             resource_ids=resources_ids)
        return resource


def find_resources(obj, resources, properties=None):
    properties = properties and list(properties) or ['id', 'name']
    for resource in resources:
        for property_name in properties:
            value = resource[property_name]
            if obj == value:
                yield resource
