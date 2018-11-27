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
import sys

from heatclient import exc

from tobiko.tests import base
from tobiko.common.managers import stack
from tobiko.common.managers import network
from tobiko.common import constants


class ScenarioTestsBase(base.TobikoTest):
    """All scenario tests inherit from this scenario base class."""

    def setUp(self):
        super(ScenarioTestsBase, self).setUp()
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.stackManager = stack.StackManager(self.clientManager,
                                               templates_dir)
        self.networkManager = network.NetworkManager(self.clientManager)
        self.params = self.default_params

        test_name = self.id()
        while test_name:
            test_module = sys.modules.get(test_name)
            if test_module:
                break
            name_parts = test_name.rsplit('.', 1)
            if len(name_parts) == 1:
                msg = "Invalid test name: {!r}".format(self.id())
                raise RuntimeError(msg)
            test_name = name_parts[0]
        self.stack_name = test_name.rsplit('.', 1)[-1]

        try:
            self.stackManager.get_stack(self.stack_name)
        except exc.HTTPNotFound:
            self.create_stack()

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
        _stack = self.stackManager.get_stack(self.stack_name)
        if not _stack:
            _stack = self.create_stack()
        return _stack
