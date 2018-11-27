# Copyright 2018 Red Hat
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

import os

from tobiko import config


# Configure HTTP proxy for connecting clients
HTTP_PROXY = config.get_any_option(
    'environ.http_proxy',
    'environ.https_proxy',
    'tempest.service_clients.proxy_url')
if (HTTP_PROXY and 'http_proxy' not in os.environ and
        'https_proxy' not in os.environ):
    os.environ.update(http_proxy=HTTP_PROXY,
                      https_proxy=HTTP_PROXY)


def get_default_credentials(api_version=None, username=None, password=None,
                            project_name=None, auth_url=None,
                            user_domain_name=None, project_domain_name=None):
    if api_version is None:
        api_version = config.get_any_option(
            'environ.OS_IDENTITY_API_VERSION',
            'tempest.identity_feature_enabled.api_v3')
        if api_version is True:
            api_version = 3
        elif api_version is False:
            api_version = 2
        elif api_version is not None:
            api_version = int(api_version)

    username = (username or
                config.get_any_option(
                    'environ.OS_USERNAME',
                    'tempest.auth.username',
                    'tempest.auth.admin_username'))
    password = (password or
                config.get_any_option(
                    'environ.OS_PASSWORD',
                    'tempest.auth.password',
                    'tempest.auth.admin_password'))
    project_name = (project_name or
                    config.get_any_option(
                        'environ.OS_PROJECT_NAME',
                        'environ.OS_TENANT_NAME',
                        'tempest.auth.project_name',
                        'tempest.auth.admin_project_name'))

    if auth_url is None and api_version in [None, 2]:
        auth_url = config.get_any_option(
            'environ.OS_AUTH_URL', 'tempest.identity.uri')
        if auth_url and api_version is None:
            api_version = get_version_from_url(auth_url)

    if auth_url is None:
        auth_url = config.get_any_option('tempest.identity.uri_v3')
        if auth_url and api_version is None:
            api_version = 3

    credentials = dict(username=username,
                       password=password,
                       project_name=project_name,
                       auth_url=auth_url)

    if api_version and api_version > 2:
        credentials.update(
            user_domain_name=(
                user_domain_name or
                config.get_any_option(
                    'environ.OS_USER_DOMAIN_NAME',
                    'tempest.auth.user_domain_name',
                    'tempest.auth.admin_domain_name')),
            project_domain_name=(
                project_domain_name or
                config.get_any_option(
                    'environ.OS_PROJECT_DOMAIN_NAME',
                    'tempest.identity.project_domain_name',
                    'tempest.auth.admin_domain_name',
                    'tempest.identity.admin_domain_name',
                    'tempest.identity.admin_tenant_name')),)

    # remove every field that is still None from credentials dictionary
    return {k: v for k, v in credentials.items() if v is not None}


def get_version_from_url(auth_url):
    if auth_url.endswith('/v2.0'):
        return 2
    elif auth_url.endswith('/v3'):
        return 3
    else:
        return None


class ClientManager(object):
    """Manages OpenStack official Python clients."""

    credentials = get_default_credentials()
    _session = None
    _heat_client = None
    _neutron_client = None

    def __init__(self, credentials=None):
        if credentials:
            self.credentials = credentials

    @property
    def session(self):
        """Returns keystone session."""
        if self._session is None:
            from keystoneauth1 import loading
            from keystoneauth1 import session
            loader = loading.get_plugin_loader('password')
            auth = loader.load_from_options(**self.credentials)
            self._session = session.Session(auth=auth, verify=False)
        return self._session

    @property
    def heat_client(self):
        if self._heat_client is None:
            from heatclient import client as heat_client
            self._heat_client = heat_client.Client(
                '1', session=self.session, endpoint_type='public',
                service_type='orchestration')
        return self._heat_client

    @property
    def neutron_client(self):
        """Returns neutron client."""
        if self._neutron_client is None:
            from neutronclient.v2_0 import client as neutron_client
            self._neutron_client = neutron_client.Client(session=self.session)
        return self._neutron_client
