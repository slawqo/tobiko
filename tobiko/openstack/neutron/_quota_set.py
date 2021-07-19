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

import json
import typing

from oslo_log import log

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack.neutron import _client


LOG = log.getLogger(__name__)


def get_neutron_quota_set(project: keystone.ProjectType = None,
                          client: _client.NeutronClientType = None,
                          detail=False,
                          **params):
    client = _client.neutron_client(client)
    project = keystone.get_project_id(project=project,
                                      session=client.httpclient.session)
    if detail:
        return client.show_quota_details(project, **params)['quota']
    else:
        return client.show_quota(project, **params)['quota']


def set_neutron_quota_set(project: keystone.ProjectType = None,
                          client: _client.NeutronClientType = None,
                          **quota):
    client = _client.neutron_client(client)
    project = keystone.get_project_id(project=project,
                                      session=client.httpclient.session)
    return client.update_quota(project, body={'quota': quota})['quota']


def ensure_neutron_quota_limits(project: keystone.ProjectType = None,
                                client: _client.NeutronClientType = None,
                                retry_timeout: tobiko.Seconds = None,
                                retry_interval: tobiko.Seconds = None,
                                **required_quotas: int) -> None:
    if not required_quotas:
        return
    client = _client.neutron_client(client)
    project = keystone.get_project_id(project=project,
                                      session=client.httpclient.session)
    for attempt in tobiko.retry(timeout=retry_timeout,
                                interval=retry_interval,
                                default_timeout=60.,
                                default_interval=3.):
        actual_limits, expected_limits = get_neutron_quota_limits_increase(
            project=project, client=client, extra_increase=10//attempt.number,
            **required_quotas)
        if expected_limits:
            if attempt.is_last:
                raise EnsureNeutronQuotaLimitsError(
                    project=project,
                    actual_limits=actual_limits,
                    expected_limits=expected_limits)
            LOG.info(f"Increase Neutron quota limit(s) (project={project}): "
                     f"{actual_limits} -> {expected_limits}...")
            try:
                set_neutron_quota_set(project=project, client=client,
                                      **expected_limits)
            except Exception as ex:
                if attempt.is_last:
                    raise
                LOG.exception("Unable to ensure Neutron quota set limits: "
                              f"{expected_limits}: {ex}")
        else:
            LOG.debug(f"Required quota limits are OK: {required_quotas}")
            break
    else:
        raise RuntimeError("Broken retry loop")


class EnsureNeutronQuotaLimitsError(tobiko.TobikoException):
    message = ("Neutron quota limits lower than "
               "expected (project={project}): "
               "{actual_limits} != {expected_limits}")


def get_neutron_quota_limits_increase(
        project: keystone.ProjectType = None,
        client: _client.NeutronClientType = None,
        extra_increase=0,
        **required_quotas: int) \
        -> typing.Tuple[typing.Dict[str, int],
                        typing.Dict[str, int]]:
    quota_set = get_neutron_quota_set(project=project,
                                      client=client,
                                      detail=True)
    LOG.debug("Got quota set:\n"
              f"{json.dumps(quota_set, indent=4, sort_keys=True)}")
    actual_limits: typing.Dict[str, int] = {}
    expected_limits: typing.Dict[str, int] = {}
    for name, needed in required_quotas.items():
        quota = quota_set[name]
        limit = int(quota['limit'])
        if limit >= 0:
            used = max(0, int(quota['used']))
            reserved = max(0, int(quota['reserved']))
            required_limit = used + reserved + needed
            if required_limit > limit:
                actual_limits[name] = limit
                expected_limits[name] = required_limit + extra_increase
    return actual_limits, expected_limits
