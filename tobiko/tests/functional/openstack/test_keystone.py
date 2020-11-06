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

from keystoneclient.v2_0 import client as v2_client
from keystoneclient.v3 import client as v3_client
from oslo_log import log
import testtools
import yaml

import tobiko
from tobiko.openstack import keystone
from tobiko.shell import sh


LOG = log.getLogger(__name__)

CIENT_CLASSSES = v2_client.Client, v3_client.Client


@keystone.skip_unless_has_keystone_credentials()
class TobikoKeystoneCredentialsCommandTest(testtools.TestCase):

    def test_execute(self):
        with sh.local_process('tobiko-keystone-credentials') as process:
            actual = yaml.full_load(process.stdout)
        process.check_exit_status()
        expected = keystone.default_keystone_credentials().to_dict()
        self.assertEqual(expected, actual)


@keystone.skip_unless_has_keystone_credentials()
class KeystoneClientAPITest(testtools.TestCase):

    def test_get_keystone_client(self):
        client = keystone.get_keystone_client()
        self.assertIsInstance(client, CIENT_CLASSSES)

    def test_list_services(self):
        services = keystone.list_services()
        self.assertTrue(services)

    def test_list_services_by_name(self):
        services = keystone.list_services(name='keystone')
        self.assertTrue(services)
        for s in services:
            self.assertEqual('keystone', s.name)

    def test_list_services_by_type(self):
        services = keystone.list_services(type='identity')
        self.assertTrue(services)
        for s in services:
            self.assertEqual('identity', s.type)

    def test_find_service(self):
        service = keystone.find_service()
        self.assertTrue(service.id)

    def test_find_service_with_unique(self):
        self.assertRaises(tobiko.MultipleObjectsFound,
                          keystone.find_service,
                          unique=True)

    def test_find_service_not_found(self):
        self.assertRaises(tobiko.ObjectNotFound,
                          keystone.find_service,
                          name='never-never-land')

    def test_find_service_with_default(self):
        service = keystone.find_service(name='never-never-land',
                                        default=None)
        self.assertIsNone(service)

    def test_find_service_by_name(self):
        service = keystone.find_service(name='keystone')
        self.assertEqual('keystone', service.name)

    def test_find_service_by_type(self):
        service = keystone.find_service(type='identity')
        self.assertEqual('identity', service.type)

    def test_list_endpoints(self):
        service = keystone.find_service(name='keystone')
        endpoints = keystone.list_endpoints()
        self.assertIn(service.id, [e.service_id for e in endpoints])

    def test_list_endpoints_by_service(self):
        service = keystone.find_service(name='keystone')
        endpoints = keystone.list_endpoints(service=service)
        self.assertTrue(endpoints)
        self.assertEqual([service.id] * len(endpoints),
                         [e.service_id for e in endpoints])

    def test_list_endpoints_by_service_id(self):
        service = keystone.find_service(name='keystone')
        endpoints = keystone.list_endpoints(service_id=service.id)
        self.assertTrue(endpoints)
        for e in endpoints:
            self.assertEqual(service.id, e.service_id)

    def test_list_endpoints_by_interface(self):
        endpoints = keystone.list_endpoints(interface='public')
        self.assertTrue(endpoints)
        for e in endpoints:
            self.assertEqual('public', e.interface)

    def test_list_endpoints_by_url(self):
        url = keystone.list_endpoints()[-1].url
        endpoints = keystone.list_endpoints(url=url)
        self.assertTrue(endpoints)
        for e in endpoints:
            self.assertEqual(url, e.url)

    def test_find_endpoint(self):
        endpoint = keystone.find_endpoint()
        self.assertTrue(endpoint.id)

    def test_find_endpoint_with_unique(self):
        self.assertRaises(tobiko.MultipleObjectsFound,
                          keystone.find_endpoint,
                          unique=True)

    def test_find_endpoint_not_found(self):
        self.assertRaises(tobiko.ObjectNotFound,
                          keystone.find_endpoint,
                          service='never-never-land')

    def test_find_endpoint_with_default(self):
        service = keystone.find_endpoint(service='never-never-land',
                                         default=None)
        self.assertIsNone(service)

    def test_find_endpoint_by_service(self):
        service = keystone.find_service(name='keystone')
        endpoint = keystone.find_endpoint(service=service)
        self.assertEqual(endpoint.service_id, service.id)

    def test_find_endpoint_by_service_id(self):
        service = keystone.find_service(name='keystone')
        endpoint = keystone.find_endpoint(service_id=service.id)
        self.assertEqual(endpoint.service_id, service.id)

    def test_find_endpoint_by_url(self):
        url = keystone.list_endpoints()[-1].url
        endpoint = keystone.find_endpoint(url=url)
        self.assertEqual(url, endpoint.url)

    def test_find_service_endpoint(self):
        service = keystone.find_service(name='keystone')
        endpoint = keystone.find_service_endpoint(name='keystone')
        self.assertEqual(service.id, endpoint.service_id)
        self.assertEqual('public', endpoint.interface)
        self.assertTrue(endpoint.enabled)

    @keystone.skip_if_missing_service(name='octavia')
    def test_find_octavia_service_endpoint(self):
        service = keystone.find_service(name='octavia')
        endpoint = keystone.find_service_endpoint(name='octavia')
        self.assertEqual(service.id, endpoint.service_id)
        self.assertEqual('public', endpoint.interface)
        self.assertTrue(endpoint.enabled)

    def test_get_session_endpoint(self):
        endpoint = keystone.get_keystone_endpoint(
            service_type='identity')
        self.assertIsInstance(endpoint, str)

    def test_get_session_token(self):
        token = keystone.get_keystone_token()
        self.assertIsInstance(token, str)
