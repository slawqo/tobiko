# Copyright 2022 Red Hat
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

import typing

from heatclient.v1 import resources

import tobiko
from tobiko.openstack.heat import _client
from tobiko.openstack.heat import _stack


RESOURCE_CLASSES = resources.Resource,
ResourceType = typing.Union[resources.Resource]


def list_resources(stack: _stack.StackIdType,
                   client: _client.HeatClientType = None,
                   **kwargs) -> tobiko.Selection[ResourceType]:
    client = _client.heat_client(client)
    stack_id = _stack.get_stack_id(stack)
    return tobiko.select(client.resources.list(stack_id=stack_id, **kwargs))


def find_resource(stack: _stack.StackIdType,
                  client: _client.HeatClientType = None,
                  unique=False,
                  **kwargs) -> ResourceType:
    _stacks = list_resources(stack=stack, client=client, **kwargs)
    if unique:
        return _stacks.unique
    else:
        return _stacks.first
