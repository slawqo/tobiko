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


def security_group_rule_list(*args, **kwargs):
    group = kwargs.pop('group', '')
    cmd = f'openstack security group rule list {{params}} {group}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def security_group_rule_show(rule, *args, **kwargs):
    cmd = f'openstack security group rule show {{params}} {rule}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def security_group_rule_create(group, *args, **kwargs):
    cmd = f'openstack security group rule create {{params}} {group}'
    kwargs['format'] = 'json'
    return _client.execute(cmd, *args, **kwargs)


def security_group_rule_delete(rules, *args, **kwargs):
    cmd = f'openstack security group rule delete {{params}} {" ".join(rules)}'
    return _client.execute(cmd, *args, **kwargs)
