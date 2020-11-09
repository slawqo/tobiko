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


def security_group_list(*args, **kwargs):
    cmd = 'openstack security group list {params}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def security_group_show(group, *args, **kwargs):
    cmd = f'openstack security group show {{params}} {group}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def security_group_create(group_name, *args, **kwargs):
    cmd = f'openstack security group create {{params}} {group_name}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def security_group_delete(groups, *args, **kwargs):
    cmd = f'openstack security group delete {{params}} {" ".join(groups)}'
    return _client.execute(cmd, *args, **kwargs)


def security_group_set(group, *args, **kwargs):
    cmd = f'openstack security group set {{params}} {group}'
    return _client.execute(cmd, *args, **kwargs)


def security_group_unset(group, *args, **kwargs):
    cmd = f'openstack security group unset {{params}} {group}'
    return _client.execute(cmd, *args, **kwargs)
