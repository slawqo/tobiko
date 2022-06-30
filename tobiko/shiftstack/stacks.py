# Copyright 2022 Red Hat
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

import netaddr

import tobiko
from tobiko.openstack import heat
from tobiko.openstack import neutron
from tobiko.openstack import nova
from tobiko.openstack import stacks
from tobiko.shiftstack import _heat
from tobiko.shiftstack import _neutron


class ShiftstackHeatStackFixture(heat.HeatStackFixture):

    def __init__(self,
                 neutron_client: neutron.NeutronClientType = None,
                 **params):
        super().__init__(**params)
        self._neutron_client = neutron_client

    def setup_client(self) -> heat.HeatClient:
        if self.client is None:
            self.client = _heat.get_shiftstack_heat_client()
        return self.client

    @property
    def neutron_client(self) -> neutron.NeutronClientType:
        if self._neutron_client is None:
            self._neutron_client = _neutron.get_shiftstack_neutron_client()
        return self._neutron_client


class ShiftstackRouterStackFixture(ShiftstackHeatStackFixture,
                                   stacks.RouterStackFixture):

    @staticmethod
    def create_router_interface(
            router: neutron.RouterIdType = None,
            subnet: neutron.SubnetIdType = None,
            network: neutron.NetworkIdType = None,
            client: neutron.NeutronClientType = None,
            add_cleanup=False) -> neutron.PortType:
        stack = ShiftstackRouterInterfaceStackFixture(
            router=router,
            subnet=subnet,
            network=network,
            neutron_client=client)
        if add_cleanup:
            tobiko.use_fixture(stack)
        else:
            tobiko.setup_fixture(stack)
        return stack.port_details


class ShiftstackRouterInterfaceStackFixture(
        ShiftstackHeatStackFixture, stacks.RouterInterfaceStackFixture):
    pass


class ShiftstackFloatingIpStackFixture(ShiftstackHeatStackFixture,
                                       stacks.FloatingIpStackFixture):
    router_stack = tobiko.required_fixture(ShiftstackRouterStackFixture)


def ensure_shiftstack_node_floating_ip(
        server: nova.ServerType,
        client: neutron.NeutronClientType = None) \
        -> netaddr.IPAddress:
    client = _neutron.shiftstack_neutron_client(client)
    fixed_ip_address = _neutron.find_shiftstack_node_ip_address(
        server=server, client=client)
    for floating_ip in neutron.list_floating_ips(client=client):
        if (netaddr.IPAddress(floating_ip['fixed_ip_address']) ==
                fixed_ip_address):
            break
    else:
        fixture = ShiftstackFloatingIpStackFixture(
            device_id=nova.get_server_id(server),
            fixed_ip_address=str(fixed_ip_address))
        floating_ip = tobiko.setup_fixture(fixture).floating_ip_details
    return netaddr.IPAddress(floating_ip['floating_ip_address'])
