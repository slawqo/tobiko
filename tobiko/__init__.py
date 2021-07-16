# Copyright 2018 Red Hat
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

from tobiko.common import _asserts
from tobiko.common import _cached
from tobiko.common import _config
from tobiko.common import _detail
from tobiko.common import _exception
from tobiko.common import _fixture
from tobiko.common import _logging
from tobiko.common.managers import loader as loader_manager
from tobiko.common import _operation
from tobiko.common import _os
from tobiko.common import _proxy
from tobiko.common import _retry
from tobiko.common import _select
from tobiko.common import _skip
from tobiko.common import _testcase
from tobiko.common import _time
from tobiko.common import _utils


TOBIKO_PACKAGE_DIR = os.path.dirname(os.path.realpath(__file__))

# Ensure any tobiko package subdir is in sys.path
for path_dir in list(sys.path):
    path_dir = os.path.realpath(path_dir)
    if path_dir.startswith(TOBIKO_PACKAGE_DIR):
        sys.path.remove(path_dir)


details_content = _detail.details_content

FailureException = _asserts.FailureException
fail = _asserts.fail

cached = _cached.cached
CachedProperty = _cached.CachedProperty

tobiko_config = _config.tobiko_config
tobiko_config_dir = _config.tobiko_config_dir
tobiko_config_path = _config.tobiko_config_path

TobikoException = _exception.TobikoException
check_valid_type = _exception.check_valid_type
exc_info = _exception.exc_info
handle_multiple_exceptions = _exception.handle_multiple_exceptions
list_exc_infos = _exception.list_exc_infos

is_fixture = _fixture.is_fixture
get_fixture = _fixture.get_fixture
fixture_property = _fixture.fixture_property
required_fixture = _fixture.required_fixture
required_setup_fixture = _fixture.required_setup_fixture
get_fixture_name = _fixture.get_fixture_name
get_fixture_class = _fixture.get_fixture_class
get_fixture_dir = _fixture.get_fixture_dir
get_object_name = _fixture.get_object_name
remove_fixture = _fixture.remove_fixture
reset_fixture = _fixture.reset_fixture
setup_fixture = _fixture.setup_fixture
cleanup_fixture = _fixture.cleanup_fixture
list_required_fixtures = _fixture.list_required_fixtures
SharedFixture = _fixture.SharedFixture
FixtureManager = _fixture.FixtureManager

CaptureLogFixture = _logging.CaptureLogFixture

load_object = loader_manager.load_object
load_module = loader_manager.load_module

makedirs = _os.makedirs
open_output_file = _os.open_output_file

runs_operation = _operation.runs_operation
before_operation = _operation.before_operation
after_operation = _operation.after_operation
with_operation = _operation.with_operation
RunsOperations = _operation.RunsOperations
Operation = _operation.Operation
get_operation = _operation.get_operation
get_operation_name = _operation.get_operation_name
operation_config = _operation.operation_config

call_proxy = _proxy.call_proxy
call_proxy_class = _proxy.call_proxy_class
list_protocols = _proxy.list_protocols
protocol = _proxy.protocol
CallHandler = _proxy.CallHandler

retry = _retry.retry
retry_attempt = _retry.retry_attempt
retry_on_exception = _retry.retry_on_exception
retry_test_case = _retry.retry_test_case
Retry = _retry.Retry
RetryAttempt = _retry.RetryAttempt
RetryCountLimitError = _retry.RetryCountLimitError
RetryLimitError = _retry.RetryLimitError
RetryTimeLimitError = _retry.RetryTimeLimitError

Selection = _select.Selection
select = _select.select
ObjectNotFound = _select.ObjectNotFound
MultipleObjectsFound = _select.MultipleObjectsFound

SkipException = _skip.SkipException
skip_if = _skip.skip_if
skip_test = _skip.skip_test
skip_unless = _skip.skip_unless
skip = _skip.skip

assert_test_case_was_skipped = _testcase.assert_test_case_was_skipped
get_test_case = _testcase.get_test_case
pop_test_case = _testcase.pop_test_case
push_test_case = _testcase.push_test_case
run_test = _testcase.run_test
TestCasesManager = _testcase.TestCasesManager

min_seconds = _time.min_seconds
max_seconds = _time.max_seconds
Seconds = _time.Seconds
SecondsValueError = _time.SecondsValueError
sleep = _time.sleep
time = _time.time
to_seconds = _time.to_seconds
to_seconds_float = _time.to_seconds_float
true_seconds = _time.true_seconds

get_short_hostname = _utils.get_short_hostname

from tobiko import config  # noqa
config.init_config()
