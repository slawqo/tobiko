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

from tobiko.openstack.heat import _client
from tobiko.openstack.heat import _template
from tobiko.openstack.heat import _stack


heat_client = _client.heat_client
default_heat_client = _client.default_heat_client
get_heat_client = _client.get_heat_client
heat_client = _client.heat_client
HeatClientFixture = _client.HeatClientFixture

heat_template = _template.heat_template
heat_template_file = _template.heat_template_file
HeatTemplateFixture = _template.HeatTemplateFixture
HeatTemplateFileFixture = _template.HeatTemplateFileFixture

HeatStackFixture = _stack.HeatStackFixture
heat_stack_parameters = _stack.heat_stack_parameters
INIT_IN_PROGRESS = _stack.INIT_IN_PROGRESS
INIT_COMPLETE = _stack.INIT_COMPLETE
INIT_IN_PROGRESS = _stack.INIT_IN_PROGRESS
CREATE_IN_PROGRESS = _stack.CREATE_IN_PROGRESS
CREATE_COMPLETE = _stack.CREATE_COMPLETE
CREATE_FAILED = _stack.CREATE_FAILED
DELETE_IN_PROGRESS = _stack.DELETE_IN_PROGRESS
DELETE_COMPLETE = _stack.DELETE_COMPLETE
DELETE_FAILED = _stack.DELETE_FAILED
