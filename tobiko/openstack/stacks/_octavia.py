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

from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack import heat
from tobiko.openstack import octavia
from tobiko.openstack.stacks import _hot
from tobiko.openstack.stacks import _neutron
from tobiko.openstack.stacks import _ubuntu
from tobiko.shell import sh

CONF = config.CONF
LOG = log.getLogger(__name__)


class AmphoraIPv4LoadBalancerStack(heat.HeatStackFixture):
    template = _hot.heat_template_file('octavia/load_balancer.yaml')

    vip_network = tobiko.required_setup_fixture(_neutron.NetworkStackFixture)

    #: Floating IP network where the Neutron floating IP are created
    @property
    def floating_network(self) -> str:
        return self.vip_network.floating_network

    @property
    def has_floating_ip(self) -> bool:
        return bool(self.floating_network)

    ip_version = 4

    provider = 'amphora'

    @property
    def vip_subnet_id(self):
        if self.ip_version == 4:
            return self.vip_network.ipv4_subnet_id
        else:
            return self.vip_network.ipv6_subnet_id

    def wait_for_active_loadbalancer(self,
                                     timeout: tobiko.Seconds = None):
        octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                                status=octavia.ACTIVE,
                                get_client=octavia.get_loadbalancer,
                                object_id=self.loadbalancer_id,
                                timeout=timeout)

    def wait_for_update_loadbalancer(self,
                                     timeout: tobiko.Seconds = None):
        octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                                status=octavia.PENDING_UPDATE,
                                get_client=octavia.get_loadbalancer,
                                object_id=self.loadbalancer_id,
                                timeout=timeout)

    def wait_for_octavia_service(self,
                                 interval: tobiko.Seconds = None,
                                 timeout: tobiko.Seconds = None,
                                 client=None):
        for attempt in tobiko.retry(timeout=timeout,
                                    interval=interval,
                                    default_timeout=180.,
                                    default_interval=5.):
            try:
                octavia.list_amphorae(loadbalancer_id=self.loadbalancer_id,
                                      client=client)
            except octavia.OctaviaClientException as ex:
                LOG.debug(f"Error listing amphorae: {ex}")
                if attempt.is_last:
                    raise
                LOG.info('Waiting for the LB to become functional again...')
            else:
                LOG.info('Octavia service is available!')
                break


class AmphoraIPv6LoadBalancerStack(AmphoraIPv4LoadBalancerStack):
    ip_version = 6


class OctaviaOtherServerStackFixture(_ubuntu.UbuntuServerStackFixture):
    pass


class HttpRoundRobinAmphoraIpv4Listener(heat.HeatStackFixture):
    template = _hot.heat_template_file('octavia/listener.yaml')

    loadbalancer = tobiko.required_setup_fixture(
        AmphoraIPv4LoadBalancerStack)

    lb_port = 80

    lb_protocol = 'HTTP'

    @property
    def loadbalancer_id(self):
        return self.loadbalancer.loadbalancer_id

    @property
    def loadbalancer_provider(self):
        return self.loadbalancer.provider

    # Pool attributes
    pool_protocol = 'HTTP'

    lb_algorithm = 'ROUND_ROBIN'

    # healthmonitor attributes
    hm_type = 'HTTP'

    hm_delay = 3

    hm_max_retries = 4

    hm_timeout = 3

    #: whenever to create the health monitor
    has_monitor = True

    @property
    def listener_id(self):
        return self.listener.listener_id

    def wait_for_active_members(self):
        for member in octavia.list_members(pool_id=self.pool_id):
            self.wait_for_active_member(pool_id=self.pool_id,
                                        member_id=member['id'])

    def wait_for_active_member(self, pool_id, member_id, **kwargs):
        """Wait for the member to be active

        Waits for the member to have an ACTIVE provisioning status.

        :param member_id: the member id.
        :param pool_id: the pool id.
        """
        octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                                status=octavia.ACTIVE,
                                get_client=octavia.get_member,
                                object_id=pool_id,
                                member_id=member_id, **kwargs)

    def wait_for_members_to_be_reachable(self,
                                         interval: tobiko.Seconds = None,
                                         timeout: tobiko.Seconds = None):

        members = [self.server_stack, self.other_server_stack]

        if len(members) < 1:
            return

        # Wait for members to be reachable from localhost
        last_reached_id = 0
        for attempt in tobiko.retry(
                timeout=timeout,
                interval=interval,
                default_interval=5.,
                default_timeout=members[0].wait_timeout):
            try:
                for member in members[last_reached_id:]:
                    octavia.check_members_balanced(
                        members_count=1,
                        ip_address=member.ip_address,
                        protocol=self.lb_protocol,
                        port=self.lb_port,
                        requests_count=1)
                    last_reached_id += 1  # prevent retrying same member again
            except sh.ShellCommandFailed:
                if attempt.is_last:
                    raise
                LOG.info(
                    "Waiting for members to have HTTP service available...")
                continue
            else:
                break
        else:
            raise RuntimeError("Members couldn't be reached!")

    # Members attributes
    server_stack = tobiko.required_fixture(_ubuntu.UbuntuServerStackFixture)

    other_server_stack = tobiko.required_setup_fixture(
        OctaviaOtherServerStackFixture)

    application_port = 80

    ip_version = 4

    @property
    def pool_id(self):
        return self.pool.pool_id

    @property
    def subnet_id(self):
        network_stack = self.server_stack.network_stack
        if self.ip_version == 4:
            return network_stack.ipv4_subnet_id
        else:
            return network_stack.ipv6_subnet_id

    @property
    def member_address(self) -> str:
        return self.get_member_address(self.server_stack)

    @property
    def other_member_address(self) -> str:
        return self.get_member_address(self.other_server_stack)

    def get_member_address(self, server_stack):
        return str(server_stack.find_fixed_ip(ip_version=self.ip_version))


class HttpRoundRobinAmphoraIpv6Listener(HttpRoundRobinAmphoraIpv4Listener):
    ip_version = 6


class HttpLeastConnectionAmphoraIpv4Listener(
      HttpRoundRobinAmphoraIpv4Listener):
    lb_algorithm = 'LEAST_CONNECTIONS'


class HttpLeastConnectionAmphoraIpv6Listener(
      HttpLeastConnectionAmphoraIpv4Listener):
    ip_version = 6


class HttpSourceIpAmphoraIpv4Listener(HttpRoundRobinAmphoraIpv4Listener):
    lb_algorithm = 'SOURCE_IP'


class HttpSourceIpAmphoraIpv6Listener(HttpSourceIpAmphoraIpv4Listener):
    ip_version = 6
    lb_protocol = 'TCP'


# OVN provider stack fixtures
class OVNIPv4LoadBalancerStack(AmphoraIPv4LoadBalancerStack):
    provider = 'ovn'


class OVNIPv6LoadBalancerStack(OVNIPv4LoadBalancerStack):
    ip_version = 6


class TcpSourceIpPortOvnIpv4Listener(HttpRoundRobinAmphoraIpv4Listener):
    loadbalancer = tobiko.required_setup_fixture(OVNIPv4LoadBalancerStack)
    lb_protocol = 'TCP'
    lb_port = 22
    has_monitor = False
    lb_algorithm = 'SOURCE_IP_PORT'
    pool_protocol = 'TCP'
    application_port = 22


class TcpSourceIpPortOvnIpv6Listener(TcpSourceIpPortOvnIpv4Listener):
    ip_version = 6
