# Copyright (c) 2022 Red Hat, Inc.
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

import testtools

import tobiko
from tobiko.openstack import keystone
from tobiko.openstack import neutron
from tobiko.openstack import stacks


@keystone.skip_unless_has_keystone_credentials()
class RouterTest(testtools.TestCase):
    """Tests network creation"""

    #: Stack of resources with a network with a gateway router
    stack = tobiko.required_fixture(stacks.NetworkStackFixture)

    def test_get_router_with_id(self):
        if not self.stack.has_gateway:
            tobiko.skip_test(f"Stack {self.stack.stack_name} has no gateway "
                             "router")
        router = neutron.get_router(self.stack.gateway_id)
        self.assertEqual(self.stack.gateway_id, router['id'])

    def test_get_router_with_details(self):
        if not self.stack.has_gateway:
            tobiko.skip_test(f"Stack {self.stack.stack_name} has no gateway "
                             "router")
        router = neutron.get_router(self.stack.gateway_details)
        self.assertEqual(self.stack.gateway_id, router['id'])

    def test_create_router(self,
                           network: neutron.NetworkIdType = None) \
            -> neutron.PortType:
        router = neutron.create_router(name=self.id(), network=network)
        self.assertIsInstance(router['id'], str)
        self.assertNotEqual('', router['id'])
        self.assertEqual(self.id(), router['name'])
        self.assertEqual(router['id'], neutron.get_router(router)['id'])
        if network is not None:
            self.assertEqual(neutron.get_network_id(network),
                             router['external_gateway_info']['network_id'])
        return router

    def test_create_router_with_network_id(self):
        network_id = self.stack.floating_network
        self.test_create_router(network=network_id)

    def test_create_router_with_network_details(self):
        network = {'id': self.stack.floating_network}
        self.test_create_router(network=network)

    def test_delete_router_with_id(self):
        router = self.test_create_router()
        neutron.delete_router(router['id'])
        self.assertRaises(neutron.NoSuchRouter, neutron.get_router,
                          router['id'])

    def test_delete_router_with_details(self):
        router = self.test_create_router()
        neutron.delete_router(router)
        self.assertRaises(neutron.NoSuchRouter, neutron.get_router,
                          router['id'])

    def test_delete_router_with_invalid_id(self):
        self.assertRaises(neutron.NoSuchRouter,
                          neutron.delete_router, '<invalid-id>')

    def test_add_router_interface_with_port(self):
        port = neutron.create_port(name=self.id())
        router = self.test_create_router()
        interface = neutron.add_router_interface(router=router, port=port)
        self.assertEqual(port['network_id'], interface['network_id'])
        return interface

    def test_remove_router_interface_with_port(self):
        interface = self.test_add_router_interface_with_port()
        neutron.remove_router_interface(router=interface['id'],
                                        port=interface['port_id'])

    def test_add_router_interface_with_subnet(self):
        network = neutron.create_network(name=self.id())
        subnet_pool_range = "172.168.111.0/24"
        subnet_pool_default_prefixlen = 26
        subnet_pool = neutron.create_subnet_pool(
            name=self.id(),
            prefixes=[subnet_pool_range],
            default_prefixlen=subnet_pool_default_prefixlen)
        subnet = neutron.create_subnet(name=self.id(),
                                       network=network,
                                       subnetpool_id=subnet_pool['id'],
                                       ip_version=4)
        router = self.test_create_router()
        interface = neutron.add_router_interface(router=router, subnet=subnet)
        self.assertEqual(subnet['id'], interface['subnet_id'])
        return interface

    def test_remove_router_interface_with_subnet(self):
        interface = self.test_add_router_interface_with_subnet()
        neutron.remove_router_interface(router=interface['id'],
                                        subnet=interface['subnet_id'])
