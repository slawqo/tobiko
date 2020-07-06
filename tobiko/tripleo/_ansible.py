# Copyright 2020 Red Hat
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

import io
import os

import yaml

import tobiko
from tobiko.shell import sh
from tobiko.tripleo import _undercloud
from tobiko.tripleo import _config


def get_tripleo_ansible_inventory():
    inventory_file = get_tripleo_ansible_inventory_file()
    with io.open(inventory_file, 'rb') as fd:
        return yaml.safe_load(fd)


def has_tripleo_ansible_inventory():
    inventory_file = get_tripleo_ansible_inventory_file()
    return inventory_file and os.path.isfile(inventory_file)


skip_if_missing_tripleo_ansible_inventory = \
    tobiko.skip_unless("Can't read TripleO Ansible inventory",
                       has_tripleo_ansible_inventory)


def get_tripleo_ansible_inventory_file():
    return tobiko.setup_fixture(TripleoAnsibleInventoryFixture).inventory_file


class TripleoAnsibleInventoryFixture(tobiko.SharedFixture):

    inventory_file = None

    def setup_fixture(self):
        tripleo = _config.get_tripleo_config()
        self.inventory_file = inventory_file = tobiko.tobiko_config_path(
            tripleo.inventory_file)
        if inventory_file and not os.path.isfile(inventory_file):
            content = read_tripleo_ansible_inventory()
            with io.open(inventory_file, 'w') as fd:
                fd.write(content)


READ_TRIPLEO_ANSIBLE_INVENTORY_SCRIPT = """
source {undercloud_rcfile} || exit 1

set -x

INVENTORY_FILE=$(mktemp tripleo-hosts-XXXXXXXXXX.yaml)
tripleo-ansible-inventory --ansible_ssh_user "{overcloud_ssh_username}" \\
                          --static-yaml-inventory "$INVENTORY_FILE"
RC=$?

if [ $RC == 0 ]; then
    cat "$INVENTORY_FILE"
fi
rm -fR "$INVENTORY_FILE"
exit $RC
"""


def read_tripleo_ansible_inventory():
    tripleo = _config.get_tripleo_config()
    ssh_client = _undercloud.undercloud_ssh_client()
    script = READ_TRIPLEO_ANSIBLE_INVENTORY_SCRIPT.format(
        undercloud_rcfile=tripleo.undercloud_rcfile,
        overcloud_ssh_username=tripleo.overcloud_ssh_username)
    return sh.execute('/bin/bash', stdin=script, ssh_client=ssh_client).stdout
