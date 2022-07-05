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

import tobiko
from tobiko import config
from tobiko import tripleo


CONF = config.CONF
PLAYBOOK_DIRNAME = os.path.join(os.path.dirname(__file__), 'playbooks')


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
        inventory = tobiko.load_yaml(inventory_yaml)
        self.assertIn('Undercloud', inventory)
        self.assertIn('Controller', inventory)
        self.assertIn('Compute', inventory)


@tripleo.skip_if_missing_tripleo_ansible_inventory
class PlaybookTest(testtools.TestCase):

    def test_ping_hosts(self):
        tripleo.run_playbook_from_undercloud(
            playbook='test_ping_hosts.yaml',
            playbook_dirname=PLAYBOOK_DIRNAME,
            roles=['ping'])

    def test_debug_vars(self):
        tripleo.run_playbook_from_undercloud(
            playbook='test_debug_vars.yaml',
            playbook_dirname=PLAYBOOK_DIRNAME,
            playbook_files=['vars/some-vars.yaml'])

    def test_undecloud_current_dir(self):
        tripleo.run_playbook_from_undercloud(
            playbook='test_undercloud_current_dir.yaml',
            playbook_dirname=PLAYBOOK_DIRNAME)

    @tripleo.skip_unless_undercloud_has_ansible(min_version=2.9)
    def test_overcloud_openstack_auth(self):
        tripleo.run_playbook_from_undercloud(
            playbook='test_overcloud_openstack_auth.yaml',
            playbook_dirname=PLAYBOOK_DIRNAME,
            requirements_files=['requirements/openstack-cloud.yaml'])
