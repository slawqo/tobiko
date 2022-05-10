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
import os

import testtools

from tobiko import shiftstack
from tobiko import tripleo


PLAYBOOK_DIRNAME = os.path.join(os.path.dirname(__file__), 'playbooks')


@tripleo.skip_if_missing_tripleo_ansible_inventory
@shiftstack.skip_unless_has_shiftstack()
class OpenShiftTest(testtools.TestCase):

    def test_ocp_cluster(self):
        clouds_file_path = shiftstack.get_clouds_file_path()
        tripleo.run_playbook_from_undercloud(
            playbook='verify-shiftstack.yaml',
            playbook_dirname=PLAYBOOK_DIRNAME,
            playbook_files=[clouds_file_path],
            requirements_files=['requirements.yaml'],
            roles=['tests'])
