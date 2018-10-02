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
from heatclient import client as heat_client
from keystoneauth1 import loading
from keystoneauth1 import session


class ClientManager(object):
    """Manages OpenStack official Python clients."""

    def __init__(self, conf):
        self.conf = conf
        self.heat_client = self.get_heat_client()

    def get_heat_client(self):
        """Returns heat client."""

        sess = self.get_session()
        return heat_client.Client('1', session=sess,
                                  endpoint_type='public',
                                  service_type='orchestration')

    def get_username(self):
        """Returns username based on config."""
        if not hasattr(self.conf.auth, 'username'):
            return self.conf.auth.admin_username
        else:
            return self.conf.auth.username

    def get_password(self):
        """Returns password based on config."""
        if not hasattr(self.conf.auth, 'password'):
            return self.conf.auth.admin_password
        else:
            return self.conf.auth.password

    def get_tenant_name(self):
        """Returns tenant/project name."""
        if hasattr(self.conf.auth, 'project_name'):
            return self.conf.auth.project_name
        else:
            return self.conf.auth.admin_project_name

    def get_user_domain_name(self):
        """Returns user domain name."""
        if hasattr(self.conf.auth, 'user_domain_name'):
            return self.conf.auth.user_domain_name
        elif hasattr(self.conf.auth, "admin_domain_name"):
            return self.conf.auth.admin_domain_name
        else:
            return self.conf.tobiko_plugin.user_domain_name

    def get_uri(self, ver=2):
        """Returns URI."""
        if ver == 3:
            if hasattr(self.conf.identity, 'uri_v3'):
                return self.conf.identity.uri_v3
        return self.conf.identity.uri

    def get_auth_version(self):
        """Returns identity/keystone API verion."""
        if hasattr(self.conf.identity_feature_enabled, 'api_v3'):
            if self.conf.identity_feature_enabled.api_v3:
                return 3
        return 2

    def get_project_domain_name(self):
        """Returns project domain name."""
        if hasattr(self.conf.identity, 'project_domain_name'):
            return self.conf.identity.project_domain_name
        elif hasattr(self.conf.auth, 'admin_domain_name'):
            return self.conf.auth.admin_domain_name
        elif hasattr(self.conf.identity, 'admin_domain_name'):
            return self.conf.identity.admin_domain_name
        elif hasattr(self.conf.identity, 'admin_tenant_name'):
            return self.conf.identity.admin_tenant_name
        else:
            return self.conf.auth.admin_domain_name

    def get_session(self):
        """Returns keystone session."""

        ver = self.get_auth_version()

        kwargs = {
            'auth_url': self.get_uri(ver),
            'username': self.get_username(),
            'password': self.get_password(),
            'project_name': self.get_tenant_name(),
        }

        if ver == 3:
            kwargs.update(
                {'user_domain_name': self.get_user_domain_name(),
                 'project_domain_name': self.get_project_domain_name()})

        with open('/tmp/stam', 'w+') as f:
            f.write(str(kwargs))

        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(**kwargs)
        return session.Session(auth=auth, verify=False)
