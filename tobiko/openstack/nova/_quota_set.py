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

from oslo_log import log

from tobiko.openstack import keystone
from tobiko.openstack.nova import _client


LOG = log.getLogger(__name__)


def get_nova_quota_set(project: keystone.ProjectType = None,
                       user: keystone.UserType = None,
                       client: _client.NovaClientType = None,
                       **params):
    client = _client.nova_client(client)
    project = keystone.get_project_id(project=project,
                                      session=client.client.session)
    user = user and keystone.get_user_id(user=user) or None
    return client.quotas.get(project, user_id=user, **params)


def set_nova_quota_set(project: keystone.ProjectType = None,
                       user: keystone.UserType = None,
                       client: _client.NovaClientType = None,
                       **params):
    client = _client.nova_client(client)
    project = keystone.get_project_id(project=project,
                                      session=client.client.session)
    user = user and keystone.get_user_id(user=user) or None
    return client.quotas.update(project, user_id=user, **params)


def ensure_nova_quota_limits(project: keystone.ProjectType = None,
                             user: keystone.UserType = None,
                             client: _client.NovaClientType = None,
                             **required: int):
    client = _client.nova_client(client)
    project = keystone.get_project_id(project=project,
                                      session=client.client.session)
    user = user and keystone.get_user_id(user=user) or None
    if user:
        # Must increase project limits before user ones
        ensure_nova_quota_limits(project=project, client=client,
                                 **required)

    quota_set = get_nova_quota_set(project=project, user=user,
                                   client=client, detail=True)
    actual_limits = {}
    increment_limits = {}
    for name, needed in required.items():
        quota = getattr(quota_set, name)
        limit: int = quota['limit']
        if limit > 0:
            in_use: int = max(0, quota['in_use']) + max(0, quota['reserved'])
            required_limit = in_use + needed
            if required_limit >= limit:
                actual_limits[name] = limit
                increment_limits[name] = required_limit + 5

    if increment_limits:
        LOG.info(f"Increment Nova quota limit(s) (project={project}, "
                 f"user={user}): {actual_limits} -> {increment_limits}...")
        try:
            set_nova_quota_set(project=project, user=user, client=client,
                               **increment_limits)
        except Exception:
            LOG.exception("Unable to ensure nova quota set limits: "
                          f"{increment_limits}")
        quota_set = get_nova_quota_set(project=project, user=user,
                                       client=client, detail=True)
        new_limits = {name: getattr(quota_set, name)['limit']
                      for name in increment_limits.keys()}

        if new_limits == actual_limits:
            LOG.error(f"Nova quota limit(s) not changed (project={project}, "
                      f"user={user}")
        else:
            LOG.info(f"Nova quota limit(s) changed (project={project}, "
                     f"user={user}): {actual_limits} -> {new_limits}...")

    return quota_set
