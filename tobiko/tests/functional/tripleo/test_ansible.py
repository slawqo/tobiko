# Copyright 2019 Red Hat
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
import yaml

from tobiko import config
from tobiko import tripleo


CONF = config.CONF


@tripleo.skip_if_missing_undercloud
class InventoryFileTest(testtools.TestCase):

    @tripleo.skip_if_missing_tripleo_ansible_inventory
    def test_get_tripleo_ansible_inventory(self):
        inventory = tripleo.get_tripleo_ansible_inventory()
        self.assertIn('Undercloud', inventory)
        self.assertIn('Controller', inventory)
        self.assertIn('Compute', inventory)

    @tripleo.skip_if_missing_tripleo_ansible_inventory
    def test_get_tripleo_ansible_inventory_file(self):
        inventory_file = tripleo.get_tripleo_ansible_inventory_file()
        self.assertTrue(os.path.isfile(inventory_file))

    def test_has_tripleo_ansible_inventory(self):
        result = tripleo.has_tripleo_ansible_inventory()
        inventory_file = tripleo.get_tripleo_ansible_inventory_file()
        self.assertIs(inventory_file and os.path.isfile(inventory_file),
                      result)

    def test_read_tripleo_ansible_inventory(self):
        inventory_yaml = tripleo.read_tripleo_ansible_inventory()
        self.assertIsInstance(inventory_yaml, str)
        self.assertTrue(inventory_yaml)
        inventory = yaml.safe_load(inventory_yaml)
        self.assertIn('Undercloud', inventory)
        self.assertIn('Controller', inventory)
        self.assertIn('Compute', inventory)
