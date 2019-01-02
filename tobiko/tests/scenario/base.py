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

from tobiko.tests import base
from tobiko.common.managers import stack as stack_manager
from tobiko.common.managers import network
from tobiko.common import clients
from tobiko.common import constants


class ScenarioTestsBase(base.TobikoTest):
    """All scenario tests inherit from this scenario base class."""

    clients = clients.ClientManager()
    default_params = constants.DEFAULT_PARAMS
    networks = network.NetworkManager(clients)
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    stacks = stack_manager.StackManager(clients, templates_dir)
    stack = None
    fault = None

    @classmethod
    def setUpClass(cls):
        super(ScenarioTestsBase, cls).setUpClass()
        cls.stack_name = cls.__module__.rsplit('.', 1)[-1]
        cls.setup_stack()

    @classmethod
    def setup_stack(cls):
        if not cls.stack:
            cls.stack = (
                cls.stacks.wait_for_stack_status(
                    stack_name=cls.stack_name,
                    check=False) or
                cls.create_stack())
        return cls.stack

    @classmethod
    def create_stack(cls, stack_name=None, template_name=None, **parameters):
        """Creates stack to be used by all scenario tests."""
        stack_name = stack_name or cls.stack_name
        template_name = template_name or stack_name + ".yaml"
        parameters = dict(cls.default_params, **parameters)
        return cls.stacks.create_stack(
            stack_name=stack_name, template_name=template_name,
            parameters=parameters)
