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
                                **required: int):
    client = _client.neutron_client(client)
    project = keystone.get_project_id(project=project,
                                      session=client.httpclient.session)

    quota_set = get_neutron_quota_set(project=project, client=client,
                                      detail=True)
    actual_limits = {}
    increment_limits = {}
    for name, needed in required.items():
        quota = quota_set[name]
        limit: int = quota['limit']
        if limit > 0:
            in_use: int = max(0, quota['used']) + max(0, quota['reserved'])
            required_limit = in_use + needed
            if required_limit >= limit:
                actual_limits[name] = limit
                increment_limits[name] = required_limit + 5

    if increment_limits:
        LOG.info(f"Increment Neutron quota limit(s) (project={project}): "
                 f"{actual_limits} -> {increment_limits}...")
        try:
            set_neutron_quota_set(project=project, client=client,
                                  **increment_limits)
        except Exception:
            LOG.exception("Unable to ensure neutron quota set limits: "
                          f"{increment_limits}")

        quota_set = get_neutron_quota_set(project=project, client=client,
                                          detail=True)
        new_limits = {name: quota_set[name]['limit']
                      for name in increment_limits.keys()}

        if new_limits == actual_limits:
            LOG.error(f"Neutron quota limit not changed (project={project})")
        else:
            LOG.info(f"Neutron quota limit changed (project={project}): "
                     f"{actual_limits} -> {new_limits}...")

    return quota_set
