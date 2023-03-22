# Copyright (c) 2023 Red Hat
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

from collections import abc
import typing

from oslo_log import log

import tobiko
from tobiko.openstack.neutron import _client


LOG = log.getLogger(__name__)
DEFAULT_SG_NAME = "default"
STATEFUL_OVN_ACTION = "allow-related"
STATELESS_OVN_ACTION = "allow-stateless"

SecurityGroupType = typing.Dict[str, typing.Any]
SecurityGroupIdOrNameType = typing.Union[str, SecurityGroupType]
SecurityGroupRuleType = typing.Dict[str, typing.Any]
SecurityGroupRuleIdType = typing.Union[str, SecurityGroupRuleType]


def list_security_groups(client=None, **params) \
        -> tobiko.Selection[SecurityGroupType]:
    security_groups = _client.neutron_client(client).list_security_groups(
        **params)
    if isinstance(security_groups, abc.Mapping):
        security_groups = security_groups['security_groups']
    return tobiko.Selection[SecurityGroupType](security_groups)


def get_security_group(sg: SecurityGroupIdOrNameType,
                       client: _client.NeutronClientType = None,
                       **params) \
        -> SecurityGroupType:
    return _client.neutron_client(client).show_security_group(
        sg, **params
    )['security_group']


def get_default_security_group(project_id, client=None, **list_params) \
        -> SecurityGroupType:
    list_params["project_id"] = project_id
    list_params["name"] = DEFAULT_SG_NAME
    sgs = list_security_groups(
        client=client, **list_params)
    return sgs.unique


def create_security_group(client=None, add_cleanup=True,
                          **params) -> SecurityGroupType:
    sg = _client.neutron_client(client).create_security_group(
        body={'security_group': params}
    )['security_group']
    if add_cleanup:
        tobiko.add_cleanup(delete_security_group,
                           sg_id=sg['id'],
                           should_exists=False,
                           client=client)

    return sg


def update_security_group(sg_id: SecurityGroupIdOrNameType,
                          client: _client.NeutronClientType = None,
                          **params) \
                              -> SecurityGroupType:
    return _client.neutron_client(client).update_security_group(
        sg_id,
        body={'security_group': params}
    )['security_group']


def delete_security_group(sg_id: SecurityGroupIdOrNameType,
                          should_exists: bool = False,
                          client: _client.NeutronClientType = None):
    try:
        _client.neutron_client(client).delete_security_group(sg_id)
    except _client.NotFound:
        if should_exists:
            raise


def create_security_group_rule(security_group_id, add_cleanup=True,
                               client=None, **rule) \
        -> SecurityGroupRuleType:
    rule['security_group_id'] = security_group_id
    sg_rule = _client.neutron_client(client).create_security_group_rule(
        body={'security_group_rule': rule}
    )['security_group_rule']

    if add_cleanup:
        tobiko.add_cleanup(delete_security_group_rule,
                           rule_id=sg_rule['id'],
                           should_exists=False,
                           client=client)

    return sg_rule


def delete_security_group_rule(rule_id: SecurityGroupRuleIdType,
                               should_exists: bool = False,
                               client: _client.NeutronClientType = None):
    try:
        _client.neutron_client(client).delete_security_group_rule(rule_id)
    except _client.NotFound:
        if should_exists:
            raise
