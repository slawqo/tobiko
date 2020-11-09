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


def port_list(*args, **kwargs):
    cmd = 'openstack port list {params}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def port_show(port, *args, **kwargs):
    cmd = f'openstack port show {{params}} {port}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def port_create(port_name, network_name, *args, **kwargs):
    cmd = f'openstack port create {{params}} --network {network_name} '\
          f'{port_name}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def port_delete(ports, *args, **kwargs):
    cmd = f'openstack port delete {{params}} {" ".join(ports)}'
    return _client.execute(cmd, *args, **kwargs)


def port_set(port, *args, **kwargs):
    cmd = f'openstack port set {{params}} {port}'
    return _client.execute(cmd, *args, **kwargs)


def port_unset(port, *args, **kwargs):
    cmd = f'openstack port unset {{params}} {port}'
    return _client.execute(cmd, *args, **kwargs)
