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

import io
import os
import typing

from oslo_log import log
import six

import tobiko
from tobiko import config
from tobiko.openstack import keystone
from tobiko.openstack import ironic
from tobiko.openstack import nova
from tobiko.shell import sh
from tobiko.shell import ssh
from tobiko.tripleo import _undercloud


CONF = config.CONF
LOG = log.getLogger(__name__)


def has_overcloud():
    # rewrite this function
    return _undercloud.has_undercloud()


def load_overcloud_rcfile():
    return _undercloud.fetch_os_env(*CONF.tobiko.tripleo.overcloud_rcfile)


skip_if_missing_overcloud = tobiko.skip_unless(
    'TripleO overcloud not configured', has_overcloud)


class OvercloudKeystoneCredentialsFixture(
        keystone.EnvironKeystoneCredentialsFixture):

    def get_environ(self):
        if has_overcloud():
            return load_overcloud_rcfile()
        else:
            return {}


def list_overcloud_nodes(**params):
    session = _undercloud.undercloud_keystone_session()
    client = nova.get_nova_client(session=session)
    return nova.list_servers(client=client, **params)


def find_overcloud_node(**params):
    session = _undercloud.undercloud_keystone_session()
    client = nova.get_nova_client(session=session)
    return nova.find_server(client=client, **params)


def power_on_overcloud_node(server: typing.Union[nova.ServerType]):
    session = _undercloud.undercloud_keystone_session()
    node_id = getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname',
                      None)
    if node_id is not None:
        client = ironic.get_ironic_client(session=session)
        try:
            ironic.power_on_node(client=client, node=node_id)
            return
        except ironic.WaitForNodePowerStateError:
            LOG.exception(f"Failed powering on Ironic node: '{node_id}'")

    client = nova.get_nova_client(session=session)
    nova.activate_server(client=client, server=server)


def power_off_overcloud_node(server: typing.Union[nova.ServerType]) \
        -> nova.NovaServer:
    session = _undercloud.undercloud_keystone_session()
    node_id = getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname',
                      None)
    if node_id is not None:
        client = ironic.get_ironic_client(session=session)
        try:
            ironic.power_off_node(client=client, node=node_id)
            return
        except ironic.WaitForNodePowerStateError:
            LOG.exception(f"Failed powering off Ironic node: '{node_id}'")

    client = nova.get_nova_client(session=session)
    nova.shutoff_server(client=client, server=server)


def overcloud_ssh_client(hostname=None, ip_version=None, network_name=None,
                         server=None, host_config=None):
    if host_config is None:
        host_config = overcloud_host_config(hostname=hostname,
                                            ip_version=ip_version,
                                            network_name=network_name,
                                            server=server)
    return ssh.ssh_client(host=hostname, host_config=host_config)


def overcloud_host_config(hostname=None, ip_version=None, network_name=None,
                          server=None):
    host_config = OvercloudHostConfig(host=hostname,
                                      ip_version=ip_version,
                                      network_name=network_name,
                                      server=server)
    return tobiko.setup_fixture(host_config)


def overcloud_node_ip_address(ip_version=None, network_name=None, server=None,
                              **params):
    server = server or find_overcloud_node(**params)
    ip_version = ip_version or CONF.tobiko.tripleo.overcloud_ip_version
    network_name = network_name or CONF.tobiko.tripleo.overcloud_network_name
    address = nova.find_server_ip_address(server=server,
                                          ip_version=ip_version,
                                          network_name=network_name)
    LOG.debug(f"Got Overcloud node address '{address}' from Undercloud "
              f"(ip_version={ip_version}, network_name={network_name}, "
              f"server={server})")
    return address


class OvercloudSshKeyFileFixture(tobiko.SharedFixture):

    @property
    def key_filename(self):
        return tobiko.tobiko_config_path(
            CONF.tobiko.tripleo.overcloud_ssh_key_filename)

    def setup_fixture(self):
        self.setup_key_file()

    def setup_key_file(self):
        key_filename = self.key_filename
        key_dirname = os.path.dirname(key_filename)
        tobiko.makedirs(key_dirname, mode=0o700)

        ssh_client = _undercloud.undercloud_ssh_client()
        _get_undercloud_file(ssh_client=ssh_client,
                             source='~/.ssh/id_rsa',
                             destination=key_filename,
                             mode=0o600)
        _get_undercloud_file(ssh_client=ssh_client,
                             source='~/.ssh/id_rsa.pub',
                             destination=key_filename + '.pub',
                             mode=0o600)


def _get_undercloud_file(ssh_client, source, destination, mode):
    content = sh.execute(['cat', source],
                         ssh_client=ssh_client).stdout
    with io.open(destination, 'wb') as fd:
        fd.write(content.encode())
    os.chmod(destination, mode)


class OvercloudHostConfig(tobiko.SharedFixture):
    host = None
    hostname = None
    port = None
    username = None
    key_file = tobiko.required_setup_fixture(OvercloudSshKeyFileFixture)
    ip_version = None
    network_name = None
    key_filename = None
    server = None

    def __init__(self, host=None, ip_version=None, network_name=None,
                 server=None, **kwargs):
        super(OvercloudHostConfig, self).__init__()
        if host:
            self.host = host
        if ip_version:
            self.ip_version = ip_version
        if network_name:
            self.network_name = network_name
        if server:
            self.server = server
            if self.host is None:
                self.host = server.name
        tobiko.check_valid_type(self.host, six.string_types)
        self._connect_parameters = ssh.gather_ssh_connect_parameters(**kwargs)

    def setup_fixture(self):
        self.hostname = str(overcloud_node_ip_address(
            name=self.host, ip_version=self.ip_version,
            network_name=self.network_name,
            server=self.server))
        self.port = self.port or CONF.tobiko.tripleo.overcloud_ssh_port
        self.username = (self.username or
                         CONF.tobiko.tripleo.overcloud_ssh_username)
        self.key_filename = self.key_filename or self.key_file.key_filename

    @property
    def connect_parameters(self):
        parameters = ssh.ssh_host_config(
            host=str(self.hostname)).connect_parameters
        parameters.update(ssh.gather_ssh_connect_parameters(self))
        parameters.update(self._connect_parameters)
        return parameters


def setup_overcloud_keystone_crederntials():
    keystone.DEFAULT_KEYSTONE_CREDENTIALS_FIXTURES.append(
        OvercloudKeystoneCredentialsFixture)


def get_overcloud_nodes_dataframe(oc_node_df_function):
    """
     :param oc_node_df_function : a function that queries a oc node
     using a cli command and returns a datraframe with an added
     hostname field.

     This function concats oc nodes dataframes into a unified overcloud
     dataframe, seperated by hostname field

    :return: dataframe of all overcloud nodes processes
    """
    import pandas
    oc_nodes_selection = list_overcloud_nodes()
    oc_nodes_names = [node.name for node in oc_nodes_selection]
    oc_nodes_dfs = [oc_node_df_function(node_name) for
                    node_name in oc_nodes_names]
    oc_procs_df = pandas.concat(oc_nodes_dfs, ignore_index=True)
    return oc_procs_df
