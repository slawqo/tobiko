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
from __future__ import absolute_import

import os

from heatclient import exc


from tobiko.tests import base
from tobiko.common.managers import stack
from tobiko.common.managers import network
from tobiko.common import constants


class ScenarioTestsBase(base.TobikoTest):
    """All scenario tests inherit from this scenario base class."""

    def setUp(self, file_path, params=None):
        super(ScenarioTestsBase, self).setUp()
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.stackManager = stack.StackManager(self.clientManager,
                                               templates_dir)
        self.networkManager = network.NetworkManager(self.clientManager)
        self.params = params or self.default_params
        file_name = os.path.basename(file_path)
        self.stack_name = file_name.split(".py")[0]

        try:
            self.stackManager.get_stack(self.stack_name)
        except exc.HTTPNotFound:
            self.create_stack(self.stack_name)

    def create_stack(self):
        """Creates stack to be used by all scenario tests."""

        # Defines parameters required by heat template

        # creates stack and stores its ID
        st = self.stackManager.create_stack(
            stack_name=self.stack_name,
            template_name="%s.yaml" % self.stack_name,
            parameters=self.params,
            status=constants.COMPLETE_STATUS)
        return st['stack']

    def _get_stack(self):
        stack = self.stackManager.get_stack(self.stack_name)
        if not stack:
            stack = self.create_stack()
        return stack
