# Copyright (c) 2021 Red Hat, Inc.
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


def network_loggable_resources_list(*args, **kwargs):
    cmd = 'openstack network loggable resources list {params}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def network_log_create(log_name, *args, **kwargs):
    cmd = f'openstack network log create {{params}} {log_name}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def network_log_show(log_name, *args, **kwargs):
    cmd = f'openstack network log show {{params}} {log_name}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def network_log_list(*args, **kwargs):
    cmd = 'openstack network log list {params}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def network_log_delete(log_names, *args, **kwargs):
    cmd = f'openstack network log delete {{params}} {" ".join(log_names)}'
    return _client.execute(cmd, *args, **kwargs)
