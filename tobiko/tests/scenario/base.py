# Copyright (c) 2018 Red Hat
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

from heatclient import exc


from tobiko.tests import base
from tobiko.common.managers import stack
from tobiko.common.managers import network
from tobiko.common import constants
from tobiko.common import clients


class ScenarioTestsBase(base.TobikoTest):
    """All scenario tests inherit from this scenario base class."""

    def setUp(self):
        super(ScenarioTestsBase, self).setUp()
        self.clientManager = clients.ClientManager(self.conf)

        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.stackManager = stack.StackManager(self.clientManager,
                                               templates_dir)
        self.networkManager = network.NetworkManager(self.clientManager)

        try:
            self.stackManager.get_stack("default")
        except exc.HTTPNotFound:
            self.create_stack()

    def create_stack(self):
        """Creates stack to be used by all scenario tests."""

        # Defines parameters required by heat template
        parameters = {'public_net': self.conf.network.floating_network_name,
                      'image': self.conf.compute.image_ref,
                      'flavor': "m1.micro"}

        # creates stack and stores its ID
        st = self.stackManager.create_stack(
            stack_name="default", template_name="default.yaml",
            parameters=parameters, wait_for_status=constants.COMPLETE_STATUS)
        return st['stack']

    def _get_stack(self, name="default"):
        stack = self.stackManager.get_stack(name)
        if not stack:
            stack = self.create_stack()
        return stack
