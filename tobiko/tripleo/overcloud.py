# Copyright 2019 Red Hat
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

import six

import tobiko
from tobiko import config
from tobiko.openstack import keystone
from tobiko.openstack import nova
from tobiko.tripleo import undercloud


CONF = config.CONF


def has_overcloud():
    # rewrite this function
    return undercloud.has_undercloud()


def load_overcloud_rcfile():
    return undercloud.fetch_os_env(rcfile=CONF.tobiko.tripleo.overcloud_rcfile)


skip_if_missing_overcloud = tobiko.skip_unless(
    'TripleO overcloud not configured', has_overcloud)


class OvercloudKeystoneCredentialsFixture(
        keystone.EnvironKeystoneCredentialsFixture):
    def get_environ(self):
        return load_overcloud_rcfile()


def list_overcloud_nodes(**params):
    session = undercloud.undercloud_keystone_session()
    client = nova.get_nova_client(session=session)
    return nova.list_servers(client=client, **params)


def find_overcloud_node(**params):
    session = undercloud.undercloud_keystone_session()
    client = nova.get_nova_client(session=session)
    return nova.find_server(client=client, **params)


def overcloud_host_config(hostname, ip_version=None, network_name=None):
    host_config = OvercloudHostConfig(host=hostname,
                                      ip_version=ip_version,
                                      network_name=network_name)
    return tobiko.setup_fixture(host_config)


def overcloud_node_ip_address(ip_version=None, network_name=None,
                              **params):
    server = find_overcloud_node(**params)
    ip_version = ip_version or CONF.tobiko.tripleo.overcloud_ip_version
    network_name = network_name or CONF.tobiko.tripleo.overcloud_network_name
    return nova.find_server_ip_address(server=server, ip_version=ip_version,
                                       network_name=network_name)


class OvercloudHostConfig(tobiko.SharedFixture):
    hostname = None
    port = None
    username = None
    key_filename = None
    ip_version = None
    network_name = None

    def __init__(self, host, ip_version=None, network_name=None):
        super(OvercloudHostConfig, self).__init__()
        tobiko.check_valid_type(host, six.string_types)
        self.host = host
        if ip_version:
            self.ip_version = ip_version
        if network_name:
            self.network_name = network_name

    def setup_fixture(self):
        self.hostname = overcloud_node_ip_address(
            name=self.host, ip_version=self.ip_version,
            network_name=self.network_name)
        self.port = CONF.tobiko.tripleo.overcloud_ssh_port
        self.username = CONF.tobiko.tripleo.overcloud_ssh_username
        self.key_filename = CONF.tobiko.tripleo.ssh_key_filename
