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


def find_resource(obj, resources, resource_type, properties=None, **params):
    if obj:
        resources = list(find_resources(obj, resources, properties=properties))
    count = len(resources)
    if count == 0:
        raise ResourceNotFound(obj=obj,
                               resource_type=resource_type,
                               properties=properties,
                               params=params)
    if count > 1:
        resource_ids = [r['id'] for r in resources]
        raise MultipleResourcesFound(obj=obj,
                                     resource_type=resource_type,
                                     properties=properties,
                                     count=len(resources),
                                     resource_ids=resource_ids,
                                     params=params)
    return resources[0]


def find_resources(obj, resources, properties=None):
    properties = properties or ('id', 'name')
    for resource in resources:
        for property_name in properties:
            value = resource[property_name]
            if obj == value:
                yield resource
                break


class ResourceNotFound(tobiko.TobikoException):
    message = ("No such {resource_type} found for obj={obj!r}, "
               "properties={properties!r} and params={params!r}")


class MultipleResourcesFound(tobiko.TobikoException):
    message = ("{count} {resource_type}s found for obj={obj!r}, "
               "properties={properties!r} and params={params!r}: "
               "{resource_ids}")
