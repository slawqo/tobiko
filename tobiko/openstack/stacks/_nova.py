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

import abc
import os
import typing
from abc import ABC

import netaddr
import six
from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack import glance
from tobiko.openstack import heat
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack.stacks import _hot
from tobiko.openstack.stacks import _neutron
from tobiko.shell import curl
from tobiko.shell import sh
from tobiko.shell import ssh


CONF = config.CONF
LOG = log.getLogger(__name__)


class KeyPairStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('nova/key_pair.yaml')
    key_file = tobiko.tobiko_config_path(CONF.tobiko.nova.key_file)
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
        key_file = self.key_file
        if not os.path.isfile(key_file):
            key_dir = os.path.dirname(key_file)
            tobiko.makedirs(key_dir)
            try:
                sh.local_execute(['ssh-keygen', '-f', key_file, '-P', ''])
            except sh.ShellCommandFailed:
                if not os.path.isfile(key_file):
                    raise
            else:
                assert os.path.isfile(key_file)


class FlavorStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('nova/flavor.yaml')

    disk: typing.Optional[int] = None
    ephemeral = None
    extra_specs = None
    is_public = None
    name = None
    rxtx_factor = None
    swap: typing.Optional[int] = None
    vcpus = None


@neutron.skip_if_missing_networking_extensions('port-security')
class ServerStackFixture(heat.HeatStackFixture, abc.ABC):

    #: Heat template file
    template = _hot.heat_template_file('nova/server.yaml')

    #: stack with the key pair for the server instance
    key_pair_stack = tobiko.required_setup_fixture(KeyPairStackFixture)

    #: stack with the internal where the server port is created
    network_stack = tobiko.required_setup_fixture(_neutron.NetworkStackFixture)

    #: whenever the server relies only on DHCP for address assignation
    @property
    def need_dhcp(self) -> bool:
        return not self.config_drive

    #: whenever the server will use config-drive to get metadata
    config_drive = False

    @property
    def image_fixture(self) -> glance.GlanceImageFixture:
        """Glance image used to create a Nova server instance"""
        raise NotImplementedError

    def delete_stack(self, stack_id=None):
        if self._outputs:
            tobiko.cleanup_fixture(self.ssh_client)
        super(ServerStackFixture, self).delete_stack(stack_id=stack_id)

    @property
    def image(self) -> str:
        return self.image_fixture.image_id

    @property
    def username(self) -> str:
        """username used to login to a Nova server instance"""
        return self.image_fixture.username or 'root'

    @property
    def password(self) -> typing.Optional[str]:
        """password used to login to a Nova server instance"""
        return self.image_fixture.password

    @property
    def connection_timeout(self) -> tobiko.Seconds:
        return self.image_fixture.connection_timeout

    @property
    def flavor_stack(self) -> FlavorStackFixture:
        """stack used to create flavor for Nova server instance"""
        raise NotImplementedError

    @property
    def flavor(self) -> str:
        """Flavor for Nova server instance"""
        return self.flavor_stack.flavor_id

    #: Whenever port security on internal network is enable
    port_security_enabled = False

    #: Security groups to be associated to network ports
    security_groups: typing.List[str] = []

    @property
    def key_name(self) -> str:
        return self.key_pair_stack.key_name

    @property
    def network(self) -> str:
        return self.network_stack.network_id

    #: Floating IP network where the Neutron floating IP are created
    @property
    def floating_network(self) -> str:
        return self.network_stack.floating_network

    @property
    def has_floating_ip(self) -> bool:
        return bool(self.floating_network)

    @property
    def ssh_client(self) -> ssh.SSHClientFixture:
        return ssh.ssh_client(host=self.ip_address,
                              username=self.username,
                              password=self.password,
                              connection_timeout=self.connection_timeout)

    @property
    def peer_ssh_client(self) -> typing.Optional[ssh.SSHClientFixture]:
        """Nearest SSH client to an host that can see server fixed IPs ports

        """
        return self.ssh_client

    @property
    def ssh_command(self) -> sh.ShellCommand:
        return ssh.ssh_command(host=self.ip_address,
                               username=self.username)

    @property
    def ip_address(self) -> str:
        if self.has_floating_ip:
            return self.floating_ip_address
        else:
            return self.outputs.fixed_ips[0]['ip_address']

    def list_fixed_ips(self, ip_version: typing.Optional[int] = None) -> \
            tobiko.Selection[netaddr.IPAddress]:
        fixed_ips: tobiko.Selection[netaddr.IPAddress] = tobiko.Selection(
            netaddr.IPAddress(fixed_ip['ip_address'])
            for fixed_ip in self.fixed_ips)
        if ip_version is not None:
            fixed_ips.with_attributes(version=ip_version)
        return fixed_ips

    def find_fixed_ip(self, ip_version: typing.Optional[int] = None,
                      unique=False) -> netaddr.IPAddress:
        fixed_ips = self.list_fixed_ips(ip_version=ip_version)
        if unique:
            return fixed_ips.unique
        else:
            return fixed_ips.first

    @property
    def fixed_ipv4(self):
        return self.find_fixed_ip(ip_version=4)

    @property
    def fixed_ipv6(self):
        return self.find_fixed_ip(ip_version=6)

    #: Schedule on different host that this Nova server instance ID
    different_host = None

    #: Schedule on same host as this Nova server instance ID
    same_host = None

    #: Scheduler group in which this Nova server is attached
    @property
    def scheduler_group(self):
        return None

    @property
    def scheduler_hints(self):
        scheduler_hints = {}
        if self.different_host:
            scheduler_hints.update(different_host=list(self.different_host))
        if self.same_host:
            scheduler_hints.update(same_host=list(self.same_host))
        if self.scheduler_group:
            scheduler_hints.update(group=self.scheduler_group)
        return scheduler_hints

    #: allow to retry creating server in case scheduler hits are not respected
    retry_create = 3
    expected_creted_status = {heat.CREATE_COMPLETE}

    def validate_created_stack(self):
        stack = super(ServerStackFixture, self).validate_created_stack()
        self.validate_scheduler_hints()
        return stack

    @property
    def hypervisor_host(self):
        return getattr(self.server_details, 'OS-EXT-SRV-ATTR:host')

    def validate_scheduler_hints(self):
        if self.scheduler_hints:
            hypervisor = self.hypervisor_host
            self.validate_same_host_scheduler_hints(hypervisor=hypervisor)
            self.validate_different_host_scheduler_hints(hypervisor=hypervisor)

    def validate_same_host_scheduler_hints(self, hypervisor):
        if self.same_host:
            different_host_hypervisors = nova.get_different_host_hypervisors(
                self.same_host, hypervisor)
            if different_host_hypervisors:
                tobiko.skip_test(f"Server {self.server_id} of stack "
                                 f"{self.stack_name} created on different "
                                 "hypervisor host from servers:\n"
                                 f"{different_host_hypervisors}")

    def validate_different_host_scheduler_hints(self, hypervisor):
        if self.different_host:
            same_host_hypervisors = nova.get_same_host_hypervisors(
                self.different_host, hypervisor)
            if same_host_hypervisors:
                tobiko.skip_test(f"Server {self.server_id} of stack "
                                 f"{self.stack_name} created on the same "
                                 "hypervisor host as servers:\n"
                                 f"{same_host_hypervisors}")

    @property
    def server_details(self):
        return nova.get_server(self.server_id)

    @property
    def port_details(self):
        return neutron.get_port(self.port_id)

    def getDetails(self):
        # pylint: disable=W0212
        details = super(ServerStackFixture, self).getDetails()
        stack = self.get_stack()
        if stack:
            details[self.fixture_name + '.stack'] = (
                self.details_content(get_json=lambda: stack._info))
            if stack.stack_status == 'CREATE_COMPLETE':
                details[self.fixture_name + '.server_details'] = (
                    self.details_content(
                        get_json=lambda: self.server_details._info))
                details[self.fixture_name + '.console_output'] = (
                    self.details_content(
                        get_text=lambda: self.console_output))
        return details

    def details_content(self, **kwargs):
        return tobiko.details_content(content_id=self.fixture_name, **kwargs)

    max_console_output_length = 64 * 1024

    @property
    def console_output(self):
        return nova.get_console_output(server=self.server_id,
                                       length=self.max_console_output_length)

    def ensure_server_status(
            self, status: str,
            retry_count: typing.Optional[int] = None,
            retry_timeout: tobiko.Seconds = None,
            retry_interval: tobiko.Seconds = None):
        self.ssh_client.close()
        for attempt in tobiko.retry(count=retry_count,
                                    timeout=retry_timeout,
                                    interval=retry_interval,
                                    default_count=3,
                                    default_timeout=900.,
                                    default_interval=5.):
            tobiko.setup_fixture(self)
            server_id = self.server_id
            try:
                server = nova.ensure_server_status(
                    server=server_id,
                    status=status,
                    timeout=attempt.time_left)
            except nova.WaitForServerStatusError:
                attempt.check_limits()
                LOG.warning(
                    f"Unable to change server '{server_id}' status to "
                    f"'{status}'",
                    exc_info=1)
                tobiko.cleanup_fixture(self)
            else:
                assert server.status == status
                break

        return server

    @property
    def nova_required_quota_set(self) -> typing.Dict[str, int]:
        requirements = super().nova_required_quota_set
        requirements['instances'] += 1
        requirements['cores'] += (self.flavor_stack.vcpus or 1)
        return requirements

    user_data = None


class CloudInitServerStackFixture(ServerStackFixture, ABC):

    #: SWAP file name
    swap_filename: str = '/swap.img'
    #: SWAP file size in bytes
    swap_size: typing.Optional[int] = None
    #: nax SWAP file size in bytes
    swap_maxsize: typing.Optional[int] = None

    @property
    def user_data(self):
        return nova.user_data(self.cloud_config)

    @property
    def cloud_config(self):
        cloud_config = nova.cloud_config()
        # default is to not create any swap files,
        # because 'swap_file_max_size' is set to None
        if self.swap_maxsize is not None:
            cloud_config = nova.cloud_config(
                cloud_config,
                swap={'filename': self.swap_filename,
                      'size': self.swap_size or 'auto',
                      'maxsize': self.swap_maxsize})
        return cloud_config

    def wait_for_cloud_init_done(self, **params):
        nova.wait_for_cloud_init_done(ssh_client=self.ssh_client,
                                      **params)


class ExternalServerStackFixture(ServerStackFixture, abc.ABC):
    # pylint: disable=abstract-method

    #: stack with the network where the server port is created
    network_stack = tobiko.required_setup_fixture(
        _neutron.ExternalNetworkStackFixture)

    # external servers doesn't need floating IPs
    has_floating_ip = False

    # We must rely on ways of configuring IPs without relying on DHCP
    config_drive = True

    # external network servers are visible from test host
    peer_ssh_client = None

    # external network DHCP could conflict with Neutron one
    need_dhcp = False

    @property
    def floating_network(self):
        return self.network_stack.network_id


class PeerServerStackFixture(ServerStackFixture, abc.ABC):
    """Server witch networking access requires passing by another Nova server
    """

    has_floating_ip = False

    @property
    def peer_stack(self) -> ServerStackFixture:
        """Peer server used to reach this one"""
        raise NotImplementedError

    @property
    def ssh_client(self) -> ssh.SSHClientFixture:
        return ssh.ssh_client(host=self.ip_address,
                              username=self.username,
                              password=self.password,
                              connection_timeout=self.connection_timeout,
                              proxy_jump=self.peer_ssh_client)

    @property
    def peer_ssh_client(self) -> ssh.SSHClientFixture:
        return self.peer_stack.ssh_client

    @property
    def ssh_command(self) -> sh.ShellCommand:
        proxy_command = self.peer_stack.ssh_command + [
            'nc', self.ip_address, '22']
        return ssh.ssh_command(host=self.ip_address,
                               username=self.username,
                               proxy_command=proxy_command)

    @property
    def network(self) -> str:
        return self.peer_stack.network


@nova.skip_if_missing_hypervisors(count=2, state='up', status='enabled')
class DifferentHostServerStackFixture(PeerServerStackFixture, abc.ABC):
    # pylint: disable=abstract-method

    @property
    def different_host(self):
        return [self.peer_stack.server_id]


class SameHostServerStackFixture(PeerServerStackFixture, abc.ABC):

    @property
    def same_host(self):
        return [self.peer_stack.server_id]


def as_str(text):
    if isinstance(text, six.string_types):
        return text
    else:
        return text.decode()


class HttpServerStackFixture(PeerServerStackFixture, abc.ABC):

    http_server_port = 80

    http_request_scheme = 'http'
    http_request_path = ''

    def send_http_request(
            self,
            hostname: typing.Union[str, netaddr.IPAddress, None] = None,
            ip_version: typing.Optional[int] = None,
            port: typing.Optional[int] = None,
            path: typing.Optional[str] = None,
            retry_count: typing.Optional[int] = None,
            retry_timeout: tobiko.Seconds = None,
            retry_interval: tobiko.Seconds = None,
            ssh_client: typing.Optional[ssh.SSHClientFixture] = None,
            **curl_parameters) -> str:
        if hostname is None:
            hostname = self.find_fixed_ip(ip_version=ip_version)
        if port is None:
            port = self.http_server_port
        if path is None:
            path = self.http_request_path
        if ssh_client is None:
            ssh_client = self.peer_stack.ssh_client
        return curl.execute_curl(scheme='http',
                                 hostname=hostname,
                                 port=port,
                                 path=path,
                                 retry_count=retry_count,
                                 retry_timeout=retry_timeout,
                                 retry_interval=retry_interval,
                                 ssh_client=ssh_client,
                                 **curl_parameters)


class ServerGroupStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('nova/server_group.yaml')


class AffinityServerGroupStackFixture(tobiko.SharedFixture):
    server_group_stack = tobiko.required_setup_fixture(
        ServerGroupStackFixture)

    @property
    def scheduler_group(self):
        return self.server_group_stack.affinity_server_group_id


class AntiAffinityServerGroupStackFixture(tobiko.SharedFixture):
    server_group_stack = tobiko.required_setup_fixture(
        ServerGroupStackFixture)

    @property
    def scheduler_group(self):
        return self.server_group_stack.anti_affinity_server_group_id
