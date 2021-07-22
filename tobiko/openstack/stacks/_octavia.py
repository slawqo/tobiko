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
from tobiko.openstack.stacks import _centos
from tobiko.openstack.stacks import _cirros
from tobiko.openstack.stacks import _hot
from tobiko.openstack.stacks import _neutron


CONF = config.CONF
LOG = log.getLogger(__name__)


class OctaviaVipNetworkStackFixture(_neutron.NetworkStackFixture):
    # Load Balancer VIP network must use port security (required by neutron to
    # support allowed address pairs on ports)
    port_security_enabled = True


class OctaviaMemberNetworkStackFixture(_neutron.NetworkStackFixture):
    pass


class OctaviaCentosServerStackFixture(_centos.CentosServerStackFixture):
    network_stack = tobiko.required_setup_fixture(
        OctaviaMemberNetworkStackFixture)

    @property
    def user_data(self):
        # Launch a webserver on port 80 that replies the server name to the
        # client
        return ("#cloud-config\n"
                "packages:\n"
                "- httpd\n"
                "runcmd:\n"
                "- [ sh, -c, \"hostname > /var/www/html/id\" ]\n"
                "- [ systemctl, enable, --now, httpd ]\n")


class OctaviaCirrosServerStackFixture(_cirros.CirrosServerStackFixture):
    network_stack = tobiko.required_setup_fixture(
        OctaviaMemberNetworkStackFixture)

    @property
    def user_data(self):
        # Launch a webserver on port 80 that replies the server name to the
        # client
        # This webserver relies on the nc command which may fail if multiple
        # clients connect at the same time. For concurrency testing,
        # OctaviaCentosServerStackFixture is more suited to handle multiple
        # requests.

        return (
            "#!/bin/sh\n"
            "sudo nc -k -p 80 -e echo -e \"HTTP/1.1 200 OK\r\n"
            "Content-Length: $(hostname | head -c-1 | wc -c )\r\n"
            "Server: $(hostname)\r\n"
            "Content-type: text/html; charset=utf-8\r\n"
            "Connection: close\r\n\r\n"
            "$(hostname)\"\n")


class OctaviaServerStackFixture(OctaviaCirrosServerStackFixture):
    pass


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

    server_stack = tobiko.required_setup_fixture(OctaviaServerStackFixture)

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


class OctaviaOtherServerStackFixture(
        OctaviaServerStackFixture):
    pass


class OctaviaOtherMemberServerStackFixture(
        OctaviaMemberServerStackFixture):
    server_stack = tobiko.required_setup_fixture(
        OctaviaOtherServerStackFixture)
