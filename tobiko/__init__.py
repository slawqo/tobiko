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

from tobiko.common.managers import fixture
from tobiko.common.managers import testcase as testcase_manager
from tobiko.common.managers import loader as loader_manager
from tobiko.common import exceptions

load_object = loader_manager.load_object
load_module = loader_manager.load_module

discover_testcases = testcase_manager.discover_testcases

is_fixture = fixture.is_fixture
get_fixture = fixture.get_fixture
get_fixture_name = fixture.get_fixture_name
get_fixture_class = fixture.get_fixture_class
get_fixture_dir = fixture.get_fixture_dir
remove_fixture = fixture.remove_fixture
setup_fixture = fixture.setup_fixture
cleanup_fixture = fixture.cleanup_fixture
list_required_fixtures = fixture.list_required_fixtures
SharedFixture = fixture.SharedFixture

TobikoException = exceptions.TobikoException
FailureException = exceptions.FailureException
