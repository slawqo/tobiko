# Copyright (c) 2019 Red Hat, Inc.
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

import os

import six
from testtools import content

import tobiko
from tobiko import config
from tobiko.openstack import heat
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack.stacks import _hot
from tobiko.openstack.stacks import _neutron
from tobiko.shell import ssh
from tobiko.shell import sh


CONF = config.CONF


class KeyPairStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('nova/key_pair.yaml')
    key_file = os.path.expanduser(CONF.tobiko.nova.key_file)
    public_key = None
    private_key = None

    def setup_fixture(self):
        self.create_key_file()
        self.read_keys()
        super(KeyPairStackFixture, self).setup_fixture()

    def read_keys(self):
        with open(self.key_file, 'r') as fd:
            self.private_key = as_str(fd.read())
        with open(self.key_file + '.pub', 'r') as fd:
            self.public_key = as_str(fd.read())

    def create_key_file(self):
        key_file = os.path.realpath(self.key_file)
        if not os.path.isfile(key_file):
            key_dir = os.path.dirname(key_file)
            if not os.path.isdir(key_dir):
                os.makedirs(key_dir)
                assert os.path.isdir(key_dir)
            try:
                sh.local_execute(['ssh-keygen', '-f', key_file, '-P', ''])
            except sh.ShellCommandFailed:
                if not os.path.isfile(key_file):
                    raise
            else:
                assert os.path.isfile(key_file)


class FlavorStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('nova/flavor.yaml')

    disk = None
    ephemeral = None
    extra_specs = None
    is_public = None
    name = None
    rxtx_factor = None
    swap = None
    vcpus = None


@neutron.skip_if_missing_networking_extensions('port-security')
class ServerStackFixture(heat.HeatStackFixture):

    #: Heat template file
    template = _hot.heat_template_file('neutron/floating_ip_server.yaml')

    #: stack with the key pair for the server instance
    key_pair_stack = tobiko.required_setup_fixture(KeyPairStackFixture)

    #: stack with the internal where the server port is created
    network_stack = tobiko.required_setup_fixture(_neutron.NetworkStackFixture)

    #: Glance image used to create a Nova server instance
    image_fixture = None

    @property
    def image(self):
        return self.image_fixture.image_id

    @property
    def username(self):
        """username used to login to a Nova server instance"""
        return self.image_fixture.username

    @property
    def password(self):
        """password used to login to a Nova server instance"""
        return self.image_fixture.password

    # Stack used to create flavor for Nova server instance
    flavor_stack = None

    @property
    def flavor(self):
        """Flavor for Nova server instance"""
        return self.flavor_stack.flavor_id

    #: Whenever port security on internal network is enable
    port_security_enabled = False

    #: Security groups to be associated to network ports
    security_groups = []

    @property
    def key_name(self):
        return self.key_pair_stack.key_name

    @property
    def network(self):
        return self.network_stack.network_id

    #: Floating IP network where the Neutron floating IP is created
    floating_network = CONF.tobiko.neutron.floating_network

    @property
    def has_floating_ip(self):
        """Whenever to allocate floating IP for the server"""
        return bool(self.floating_network)

    @property
    def ssh_client(self):
        return ssh.ssh_client(host=self.ip_address,
                              username=self.username,
                              password=self.password)

    @property
    def ssh_command(self):
        return ssh.ssh_command(host=self.ip_address,
                               username=self.username)

    @property
    def ip_address(self):
        if self.has_floating_ip:
            return self.floating_ip_address
        else:
            return self.outputs.fixed_ips[0]['ip_address']

    #: Schedule on different host that this Nova server instance ID
    different_host = None

    #: Schedule on same host as this Nova server instance ID
    same_host = None

    @property
    def scheduler_hints(self):
        scheduler_hints = {}
        if self.different_host:
            scheduler_hints.update(different_host=self.different_host)
        if self.same_host:
            scheduler_hints.update(same_host=self.same_host)
        return scheduler_hints

    @property
    def server_details(self):
        return nova.get_server(self.server_id)

    max_console_output_length = 64 * 1024

    def getDetails(self):
        server_id = content.Content(
            content.UTF8_TEXT, lambda: [self.server_id.encode()])
        console_output = content.Content(
            content.UTF8_TEXT, lambda: [self.console_output.encode()])
        return {self.stack_name + '.server_id': server_id,
                self.stack_name + '.console_output': console_output}

    @property
    def console_output(self):
        return nova.get_console_output(server=self.server_id,
                                       length=self.max_console_output_length)


class PeerServerStackFixture(ServerStackFixture):
    """Server witch networking access requires passing by a peer Nova server
    """

    has_floating_ip = False

    #: Peer server used to reach this one
    peer_stack = None

    @property
    def ssh_client(self):
        return ssh.ssh_client(host=self.ip_address,
                              username=self.username,
                              password=self.password,
                              proxy_jump=self.peer_stack.ssh_client)

    @property
    def ssh_command(self):
        proxy_command = self.peer_stack.ssh_command + [
            'nc', self.ip_address, '22']
        return ssh.ssh_command(host=self.ip_address,
                               username=self.username,
                               proxy_command=proxy_command)


@nova.skip_if_missing_hypervisors(count=2, state='up', status='enabled')
class DifferentHostServerStackFixture(PeerServerStackFixture):

    @property
    def different_host(self):
        return [self.peer_stack.server_id]


class SameHostServerStackFixture(PeerServerStackFixture):

    @property
    def same_host(self):
        return [self.peer_stack.server_id]


def as_str(text):
    if isinstance(text, six.string_types):
        return text
    else:
        return text.decode()
