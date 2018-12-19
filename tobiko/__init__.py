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

from tobiko.common.managers import fixture as fixture_manager
from tobiko.common.managers import testcase as testcase_manager
from tobiko.common.managers import loader as loader_manager


load_object = loader_manager.load_object
load_module = loader_manager.load_module

discover_testcases = testcase_manager.discover_testcases

Fixture = fixture_manager.Fixture
fixture = fixture_manager.fixture
is_fixture = fixture_manager.is_fixture
get_fixture = fixture_manager.get_fixture
create_fixture = fixture_manager.create_fixture
delete_fixture = fixture_manager.delete_fixture
get_required_fixtures = fixture_manager.get_required_fixtures
discover_required_fixtures = fixture_manager.discover_required_fixtures
create_fixtures = fixture_manager.create_fixtures
delete_fixtures = fixture_manager.delete_fixtures
