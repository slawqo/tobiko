# Copyright 2021 Red Hat
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

from keystoneclient import base
from keystoneclient.v2_0 import tenants as tenants_v2
from keystoneclient.v2_0 import users as users_v2
from keystoneclient.v3 import projects as projects_v3
from keystoneclient.v3 import users as users_v3


KeystoneResourceType = typing.Union[str, base.Resource]
ProjectType = typing.Union[str, tenants_v2.Tenant, projects_v3.Project]
UserType = typing.Union[str, users_v2.User, users_v3.User]


def get_project_id(
        project: typing.Optional[ProjectType] = None,
        session=None) -> str:
    if project is not None:
        return get_keystone_resource_id(project)
    if session is not None:
        return session.get_project_id()
    raise ValueError("'project' and 'session' can't be None ata the same "
                     "time.")


def get_user_id(
        user: typing.Optional[UserType] = None,
        session=None) -> str:
    if user is not None:
        return get_keystone_resource_id(user)
    if session is not None:
        return session.get_user_id()
    raise ValueError("'project' and 'session' can't be None ata the same "
                     "time.")


def get_keystone_resource_id(resource: KeystoneResourceType) -> str:
    if isinstance(resource, str):
        return resource

    if isinstance(resource, base.Resource):
        return resource.id

    raise TypeError(f"Object {resource} is not a valid Keystone resource "
                    "type")
