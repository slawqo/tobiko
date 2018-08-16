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
        return heat_client.Client('1', session=sess)

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

    def get_session(self):
        """Returns keystone session."""
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(
            auth_url=self.conf.identity.uri,
            username=self.get_username(),
            password=self.get_password(),
            project_name=self.conf.auth.admin_project_name)
        return session.Session(auth=auth)
