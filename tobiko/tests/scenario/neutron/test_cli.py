# Copyright (c) 2019 Red Hat
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

import random

import testtools
from oslo_log import log

from tobiko.openstack import neutron
from tobiko.openstack import openstackclient


LOG = log.getLogger(__name__)


class BaseCliTest(testtools.TestCase):

    def setUp(self):
        super(BaseCliTest, self).setUp()
        self.api = neutron.get_neutron_client()

    def api_network_delete(self, network):
        nets = self.api.list_networks()['networks']
        for net in nets:
            if net['name'] == network:
                self.api.delete_network(net['id'])
                break
            if net['id'] == network:
                self.api.delete_network(network)
                break

    def api_subnet_delete(self, subnet_name):
        subnets = self.api.list_subnets()['subnets']
        for subnet in subnets:
            if subnet['name'] == subnet_name:
                self.api.delete_subnet(subnet['id'])
                break
            if subnet['id'] == subnet_name:
                self.api.delete_subnet(subnet_name)
                break

    def api_port_delete(self, port_name):
        ports = self.api.list_ports()['ports']
        for port in ports:
            if port['name'] == port_name:
                self.api.delete_port(port['id'])
                break
            if port['id'] == port_name:
                self.api.delete_port(port_name)
                break

    def api_random_port_create(self):
        net_name = self.random_name()
        port_name = self.random_name()
        network = self.api.create_network({'network': {'name': net_name}})
        self.addCleanup(self.api_network_delete, net_name)
        network_id = network['network']['id']
        self.api.create_port({'port': {'name': port_name,
                                       'network_id': network_id}})
        self.addCleanup(self.api_port_delete, port_name)
        return port_name

    def api_random_subnet_create(self):
        net_name = self.random_name()
        subnet_name = self.random_name()
        network = self.api.create_network({'network': {'name': net_name}})
        self.addCleanup(self.api_network_delete, net_name)
        network_id = network['network']['id']
        self.api.create_subnet({'subnet': {'name': subnet_name,
                                           'network_id': network_id,
                                           'ip_version': 4,
                                           'cidr': '123.123.123.0/24'}})
        return subnet_name

    def api_random_network_create(self):
        name = self.random_name()
        self.api.create_network({'network': {'name': name}})
        self.addCleanup(self.api_network_delete, name)
        return name

    def random_name(self, length=16):
        letters = 'abcdefghijklmnopqrstuvwxyz'
        random_string = ''.join(random.choice(letters) for i in range(length))
        return f'{self.__class__.__name__}-{random_string}'


class NeutronCliNetwork(BaseCliTest):

    def test_network_creation(self):
        net_name = self.random_name()
        output = openstackclient.network_create(net_name)
        self.addCleanup(self.api_network_delete, net_name)
        self.assertEqual(output['name'], net_name)  # pylint: disable=E1126
        self.assertEqual(output['status'], 'ACTIVE')  # pylint: disable=E1126

    def test_network_deletion(self):
        net_name_1 = self.api_random_network_create()
        net_name_2 = self.api_random_network_create()
        openstackclient.network_delete([net_name_1, net_name_2])
        nets = self.api.list_networks()['networks']
        for net in nets:
            self.assertNotEqual(net['name'], net_name_1)
            self.assertNotEqual(net['name'], net_name_2)

    def test_network_list(self):
        net_name = self.api_random_network_create()
        nets = openstackclient.network_list()
        found = False
        for net in nets:
            if net['Name'] == net_name:
                found = True
                break
        self.assertTrue(found)

    def test_network_show(self):
        net_name = self.api_random_network_create()
        net = openstackclient.network_show(net_name)
        self.assertEqual(net['name'], net_name)  # pylint: disable=E1126


class NeutronCliSubnet(BaseCliTest):

    def test_subnet_creation(self):
        subnet_name = self.random_name()
        net_name = self.api_random_network_create()
        output = openstackclient.subnet_create(
                subnet_name, net_name, **{'subnet-range': '123.123.123.0/24'})
        self.assertEqual(output['name'], subnet_name)  # pylint: disable=E1126

    def test_subnet_deletion(self):
        subnet_name_1 = self.api_random_subnet_create()
        subnet_name_2 = self.api_random_subnet_create()
        openstackclient.subnet_delete([subnet_name_1, subnet_name_2])
        subnets = self.api.list_subnets()['subnets']
        for subnet in subnets:
            self.assertNotEqual(subnet['name'], subnet_name_1)
            self.assertNotEqual(subnet['name'], subnet_name_2)

    def test_subnet_list(self):
        subnet_name = self.api_random_subnet_create()
        subnets = openstackclient.subnet_list()
        found = False
        for subnet in subnets:
            if subnet['Name'] == subnet_name:
                found = True
                break
        self.assertTrue(found)

    def test_subnet_show(self):
        subnet_name = self.api_random_subnet_create()
        subnet = openstackclient.subnet_show(subnet_name)
        self.assertEqual(subnet['name'], subnet_name)  # pylint: disable=E1126


class NeutronCliPort(BaseCliTest):

    def test_port_creation(self):
        port_name = self.random_name()
        net_name = self.api_random_network_create()
        output = openstackclient.port_create(port_name, net_name)
        self.addCleanup(self.api_port_delete, port_name)
        self.assertEqual(output['name'], port_name)  # pylint: disable=E1126

    def test_port_deletion(self):
        port_name_1 = self.api_random_port_create()
        port_name_2 = self.api_random_port_create()
        openstackclient.port_delete([port_name_1, port_name_2])
        ports = self.api.list_ports()['ports']
        for port in ports:
            self.assertNotEqual(port['name'], port_name_1)
            self.assertNotEqual(port['name'], port_name_2)

    def test_port_list(self):
        port_name = self.api_random_port_create()
        ports = openstackclient.port_list()
        found = False
        for port in ports:
            if port['Name'] == port_name:
                found = True
                break
        self.assertTrue(found)

    def test_port_show(self):
        port_name = self.api_random_port_create()
        port = openstackclient.port_show(port_name)
        self.assertEqual(port['name'], port_name)  # pylint: disable=E1126
