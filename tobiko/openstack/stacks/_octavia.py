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
from tobiko.openstack.stacks import _cirros
from tobiko.openstack.stacks import _hot
from tobiko.openstack.stacks import _neutron
from tobiko.openstack.stacks import _ubuntu


CONF = config.CONF
LOG = log.getLogger(__name__)


class OctaviaVipNetworkStackFixture(_neutron.NetworkStackFixture):
    # Load Balancer VIP network must use port security (required by neutron to
    # support allowed address pairs on ports)
    port_security_enabled = True


class OctaviaLoadbalancerStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('octavia/load_balancer.yaml')

    vip_network = tobiko.required_setup_fixture(OctaviaVipNetworkStackFixture)

    ip_version = 4

    @property
    def vip_subnet_id(self):
        if self.ip_version == 4:
            return self.vip_network.ipv4_subnet_id
        else:
            return self.vip_network.ipv6_subnet_id


class OctaviaListenerStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('octavia/listener.yaml')

    loadbalancer = tobiko.required_setup_fixture(
        OctaviaLoadbalancerStackFixture)

    lb_port = 80

    lb_protocol = 'HTTP'

    @property
    def loadbalancer_id(self):
        return self.loadbalancer.loadbalancer_id


class OctaviaPoolStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('octavia/pool.yaml')

    listener = tobiko.required_setup_fixture(
        OctaviaListenerStackFixture)

    pool_protocol = 'HTTP'

    lb_algorithm = 'ROUND_ROBIN'

    hm_type = 'HTTP'

    # healthmonitor attributes
    hm_delay = 3

    hm_max_retries = 4

    hm_timeout = 3

    hm_type = 'HTTP'

    @property
    def listener_id(self):
        return self.listener.listener_id


class OctaviaMemberServerStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('octavia/member.yaml')

    pool = tobiko.required_setup_fixture(OctaviaPoolStackFixture)

    @property
    def server_stack(self):
        return tobiko.setup_fixture(_ubuntu.UbuntuServerStackFixture,
                                    fixture_id=self.fixture_id)

    application_port = 80

    ip_version = 4

    @property
    def pool_id(self):
        return self.pool.pool_id

    @property
    def subnet_id(self):
        if self.ip_version == 4:
            return self.server_stack.network_stack.ipv4_subnet_id
        else:
            return self.server_stack.network_stack.ipv6_subnet_id

    @property
    def member_address(self):
        return [
            fixed_ip['ip_address']
            for fixed_ip in self.server_stack.fixed_ips
            if ((self.ip_version == 4 and
                 ':' not in fixed_ip['ip_address']) or
                (self.ip_version == 6 and
                 ':' in fixed_ip['ip_address']))
        ][0]


class OctaviaClientServerStackFixture(_cirros.CirrosServerStackFixture):
    network_stack = tobiko.required_setup_fixture(
        OctaviaVipNetworkStackFixture)
