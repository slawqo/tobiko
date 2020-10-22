# Copyright (c) 2020 Red Hat, Inc.
#
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

from tobiko.openstack.openstackclient import _client


def subnet_list(*args, **kwargs):
    cmd = 'openstack subnet list {params}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def subnet_show(subnet, *args, **kwargs):
    cmd = f'openstack subnet show {{params}} {subnet}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def subnet_create(subnet_name, network_name, *args, **kwargs):
    cmd = f'openstack subnet create {{params}} --network '\
          f'{network_name} {subnet_name}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def subnet_delete(subnets, *args, **kwargs):
    cmd = f'openstack subnet delete {{params}} {" ".join(subnets)}'
    return _client.execute(cmd, *args, **kwargs)


def subnet_set(subnet, *args, **kwargs):
    cmd = f'openstack subnet set {{params}} {subnet}'
    return _client.execute(cmd, *args, **kwargs)


def subnet_unset(subnet, *args, **kwargs):
    cmd = f'openstack subnet unset {{params}} {subnet}'
    return _client.execute(cmd, *args, **kwargs)
