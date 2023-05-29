# Copyright (c) 2023 Red Hat, Inc.
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

import openstack

import tobiko
from tobiko import config
from tobiko.openstack import keystone


CONF = config.CONF


class OpenstacksdkClientFixture(tobiko.SharedFixture):

    client = None

    def __init__(self, client=None):
        super(OpenstacksdkClientFixture, self).__init__()
        if client:
            self.client = client

    def setup_fixture(self):
        self.setup_client()

    def setup_client(self):
        client = self.client
        # create a new connection if it was not created before or if TLS-e is
        # enabled (otherwise, an SSLError exception is raised)
        if not client:
            credentials = keystone.keystone_credentials()
            tmp_auth = {
                'os-auth-url': credentials.auth_url,
                'os-password': credentials.password,
                'os-username': credentials.username,
                'os-cacert': credentials.cacert,
                'os-project-name': credentials.project_name,
                'os-user-domain-name': credentials.user_domain_name,
                'os-project-domain-name': credentials.project_domain_name,
                'os-project-domain-id': credentials.project_domain_id
            }
            if credentials.api_version == 3:
                tmp_auth['os-identity-api-version'] = credentials.api_version
            if 'https://' in credentials.auth_url and not credentials.cacert:
                tmp_auth['os-cacert'] = \
                    CONF.tobiko.tripleo.undercloud_cacert_file
            self.client = client = openstack.connect(**tmp_auth)
        return client


def openstacksdk_client():
    fixture = tobiko.setup_fixture(OpenstacksdkClientFixture())
    return fixture.client
