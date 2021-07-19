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

from oslo_log import log

import tobiko
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
                             retry_timeout: tobiko.Seconds = None,
                             retry_interval: tobiko.Seconds = None,
                             **required_quotas: int):
    if not required_quotas:
        return

    client = _client.nova_client(client)
    project = keystone.get_project_id(project=project,
                                      session=client.client.session)
    user = user and keystone.get_user_id(user=user) or None
    if user:
        # Must increase project limits before user ones
        ensure_nova_quota_limits(project=project, client=client,
                                 **required_quotas)

    for attempt in tobiko.retry(timeout=retry_timeout,
                                interval=retry_interval,
                                default_timeout=60.,
                                default_interval=3.):
        actual_limits, expected_limits = get_nova_quota_limits_increase(
            project=project, user=user, client=client,
            extra_increase=10//attempt.number, **required_quotas)
        if expected_limits:
            if attempt.is_last:
                raise EnsureNovaQuotaLimitsError(
                    project=project,
                    actual_limits=actual_limits,
                    expected_limits=expected_limits)
            LOG.info(f"Increase Nova quota limit(s) (project={project}, "
                     f"user={user}): {actual_limits} -> {expected_limits}...")
            try:
                set_nova_quota_set(project=project, user=user, client=client,
                                   **expected_limits)
            except Exception:
                if attempt.is_last:
                    raise
                LOG.exception("Error increasing Nova quota set limits: "
                              f"{expected_limits}")
        else:
            LOG.debug(f"Required Nova quota limits are OK: {required_quotas}")
            break
    else:
        raise RuntimeError("Broken retry loop")


class EnsureNovaQuotaLimitsError(tobiko.TobikoException):
    message = ("Neutron quota limits lower than "
               "expected (project={project}): "
               "{actual_limits} != {expected_limits}")


def get_nova_quota_limits_increase(
        project: keystone.ProjectType = None,
        user: keystone.UserType = None,
        client: _client.NovaClientType = None,
        extra_increase=0,
        **required_quotas: int) \
        -> typing.Tuple[typing.Dict[str, int],
                        typing.Dict[str, int]]:
    quota_set = get_nova_quota_set(project=project, user=user,
                                   client=client, detail=True)
    LOG.debug("Got Nova quota set:\n"
              f"{quota_set}")
    actual_limits: typing.Dict[str, int] = {}
    expected_limits: typing.Dict[str, int] = {}
    for name, needed in required_quotas.items():
        quota = getattr(quota_set, name)
        limit: int = int(quota['limit'])
        if limit >= 0:
            in_use = max(0, int(quota['in_use']))
            reserved = max(0, int(quota['reserved']))
            required_limit = in_use + reserved + needed
            if required_limit >= limit:
                actual_limits[name] = limit
                expected_limits[name] = required_limit + extra_increase
    return actual_limits, expected_limits
