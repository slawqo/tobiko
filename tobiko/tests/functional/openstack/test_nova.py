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

import testtools

import tobiko

from tobiko.openstack import nova
from tobiko.openstack import stacks


class KeyPairTest(testtools.TestCase):

    stack = tobiko.required_setup_fixture(stacks.KeyPairStackFixture)

    def test_key_files(self):
        self.assertTrue(os.path.isfile(self.stack.key_file))
        self.assertTrue(os.path.isfile(self.stack.key_file + '.pub'))


class ClientTest(testtools.TestCase):

    def test_list_hypervisors(self):
        hypervisors = nova.list_hypervisors()
        self.assertTrue(hypervisors)
        self.assertEqual(1, hypervisors[0].id)
        self.assertTrue(hasattr(hypervisors[0], 'cpu_info'))

    def test_list_hypervisors_without_details(self):
        hypervisors = nova.list_hypervisors(detailed=False)
        self.assertTrue(hypervisors)
        self.assertEqual(1, hypervisors[0].id)
        self.assertFalse(hasattr(hypervisors[0], 'cpu_info'))

    def test_list_hypervisors_with_hypervisor_hostname(self):
        hypervisor = nova.list_hypervisors()[0]
        hypervisors = nova.list_hypervisors(
            hypervisor_hostname=hypervisor.hypervisor_hostname)
        self.assertEqual([hypervisor], hypervisors)


class HypervisorTest(testtools.TestCase):

    def test_skip_if_missing_hypervisors(self, count=1, should_skip=False,
                                         **params):
        if should_skip:
            expected_exeption = self.skipException
        else:
            expected_exeption = self.failureException

        @nova.skip_if_missing_hypervisors(count=count, **params)
        def method():
            raise self.fail('Not skipped')

        exception = self.assertRaises(expected_exeption, method)
        if should_skip:
            hypervisors = nova.list_hypervisors(**params)
            message = "missing {!r} hypervisor(s)".format(
                count - len(hypervisors))
            if params:
                message += " with {!s}".format(
                    ','.join('{!s}={!r}'.format(k, v)
                             for k, v in params.items()))
            self.assertEqual(message, str(exception))
        else:
            self.assertEqual('Not skipped', str(exception))

    def test_skip_if_missing_hypervisors_with_no_hypervisors(self):
        self.test_skip_if_missing_hypervisors(id=-1,
                                              should_skip=True)

    def test_skip_if_missing_hypervisors_with_big_count(self):
        self.test_skip_if_missing_hypervisors(count=1000000,
                                              should_skip=True)
