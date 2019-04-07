# Copyright (c) 2019 Red Hat
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

import tobiko
from tobiko import config
from tobiko.openstack import heat
from tobiko.tests import base

CONF = config.CONF


TEMPLATE_DIRS = [os.path.join(os.path.dirname(__file__), 'templates')]


def heat_template_file(template_file):
    return heat.heat_template_file(template_file=template_file,
                                   template_dirs=TEMPLATE_DIRS)


class InternalNetworkFixture(heat.HeatStackFixture):
    template = heat_template_file('internal_network.yaml')
    floating_network = CONF.tobiko.neutron.floating_network


class SecurityGroupsFixture(heat.HeatStackFixture):
    template = heat_template_file('security_groups.yaml')


class NeutronTest(base.TobikoTest):

    def setup_fixture(self, fixture_type):
        stack = tobiko.setup_fixture(fixture_type)
        stack.wait_for_outputs()
        return stack
