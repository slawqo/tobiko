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

import logging
import os
import sys
import traceback
import typing  # noqa

from oslo_log import log
import testtools

from tobiko.common import _config
from tobiko.common import _exception
from tobiko.common import _itimer
from tobiko.common import _logging
from tobiko.common import _time


LOG = log.getLogger(__name__)

os.environ.setdefault('PYTHON', sys.executable)


class TestCasesFinder(object):

    def __init__(self, config=None, repo_type=None, repo_url=None,
                 test_path=None, top_dir=None, group_regex=None,
                 blacklist_file=None, whitelist_file=None, black_regex=None,
                 filters=None):
        """
        :param str config: The path to the stestr config file. Must be a
            string.
        :param str repo_type: This is the type of repository to use. Valid
            choices are 'file' and 'sql'.
        :param str repo_url: The url of the repository to use.
        :param str test_path: Set the test path to use for unittest discovery.
            If both this and the corresponding config file option are set, this
            value will be used.
        :param str top_dir: The top dir to use for unittest discovery. This
            takes precedence over the value in the config file. (if one is
            present in the config file)
        :param str group_regex: Set a group regex to use for grouping tests
            together in the stestr scheduler. If both this and the
            corresponding config file option are set this value will be used.
        :param str blacklist_file: Path to a blacklist file, this file contains
            a separate regex exclude on each newline.
        :param str whitelist_file: Path to a whitelist file, this file contains
            a separate regex on each newline.
        :param str black_regex: Test rejection regex. If a test cases name
            matches on re.search() operation, it will be removed from the final
            test list.
        :param list filters: A list of string regex filters to initially apply
            on the test list. Tests that match any of the regexes will be used.
            (assuming any other filtering specified also uses it)
        """

        self.config = config or '.stestr.conf'
        self.repo_type = repo_type or 'file'
        self.repo_url = repo_url
        self.test_path = test_path
        self.top_dir = top_dir
        self.group_regex = group_regex
        self.blacklist_file = blacklist_file
        self.whitelist_file = whitelist_file
        self.black_regex = black_regex
        self.filters = filters

    def discover_test_cases(self, **kwargs):
        """Iterate over test_ids for a project
        This method will print the test_ids for tests in a project. You can
        filter the output just like with the run command to see exactly what
        will be run.
        """
        from stestr import config_file

        params = dict(config=self.config, repo_type=self.repo_type,
                      repo_url=self.repo_url, test_path=self.test_path,
                      top_dir=self.top_dir, group_regex=self.group_regex,
                      blacklist_file=self.blacklist_file,
                      whitelist_file=self.whitelist_file,
                      black_regex=self.black_regex, filters=self.filters)
        if kwargs:
            params.update(kwargs)
        ids = None
        config = params.pop('config')
        conf = config_file.TestrConf(config)
        filters = params.pop('filters')
        blacklist_file = params.pop('blacklist_file')
        whitelist_file = params.pop('whitelist_file')
        black_regex = params.pop('black_regex')
        cmd = conf.get_run_command(
            regexes=filters, repo_type=params['repo_type'],
            repo_url=params['repo_url'], group_regex=params['group_regex'],
            blacklist_file=blacklist_file, whitelist_file=whitelist_file,
            black_regex=black_regex, test_path=params['test_path'],
            top_dir=params['top_dir'])
        not_filtered = filters is None and blacklist_file is None\
            and whitelist_file is None and black_regex is None

        try:
            cmd.setUp()
            # List tests if the fixture has not already needed to to filter.
            if not_filtered:
                ids = cmd.list_tests()
            else:
                ids = cmd.test_ids
        except SystemExit as ex:
            raise RuntimeError("Error discovering test cases IDs with "
                               f"parameters: {params}") from ex
        finally:
            cmd.cleanUp()

        return sorted(ids)


FINDER = TestCasesFinder()


def discover_test_cases(finder=FINDER, **kwargs):
    return finder.discover_test_cases(**kwargs)


class TestCaseTimeoutError(_exception.TobikoException):
    message = ("Test case '{testcase_id}' timed out after {timeout} seconds "
               "at:\n{stack}")


class TestCase(testtools.TestCase):

    _capture_log = False
    _capture_log_level = logging.DEBUG
    _capture_log_logger = logging.root
    _testcase_timeout: _time.Seconds = None

    @classmethod
    def setUpClass(cls):
        super(TestCase, cls).setUpClass()
        config = _config.tobiko_config()
        cls._capture_log = config.logging.capture_log
        cls._testcase_timeout = _time.to_seconds(cls._testcase_timeout or
                                                 config.testcase.timeout or
                                                 None)

    def setUp(self):
        super(TestCase, self).setUp()
        self._push_test_case()
        self._setup_capture_log()
        self._setup_testcase_timeout()

    def _setup_capture_log(self):
        if self._capture_log:
            self.useFixture(_logging.CaptureLogFixture(
                test_case_id=self.id(),
                level=self._capture_log_level,
                logger=self._capture_log_logger))

    def _setup_testcase_timeout(self):
        timeout = self._testcase_timeout
        if timeout is not None:
            self.useFixture(_itimer.itimer(
                delay=timeout,
                on_timeout=self._on_testcase_timeout))

    def _on_testcase_timeout(self, _signal_number, frame):
        stack = traceback.extract_stack(frame)
        for test_method_index, summary in enumerate(stack):
            if self._testMethodName == summary.name:
                stack = stack[test_method_index:]
                break

        formatted_stack = ''.join(traceback.format_list(stack))
        timeout = self._testcase_timeout
        raise TestCaseTimeoutError(testcase_id=self.id(), timeout=timeout,
                                   stack=formatted_stack)

    def _push_test_case(self):
        push_test_case(self)
        self.addCleanup(self._pop_test_case)

    def _pop_test_case(self):
        self.assertIs(self, pop_test_case())


class TestCasesManager(object):

    def __init__(self):
        self._test_cases: typing.List[TestCase] = []

    def get_test_case(self) -> TestCase:
        try:
            return self._test_cases[-1]
        except IndexError:
            return DUMMY_TEST_CASE

    def pop_test_case(self) -> TestCase:
        return self._test_cases.pop()

    def push_test_case(self, test_case: TestCase):
        _exception.check_valid_type(test_case, TestCase)
        self._test_cases.append(test_case)


TEST_CASES = TestCasesManager()


def push_test_case(test_case: testtools.TestCase,
                   manager: TestCasesManager = TEST_CASES):
    return manager.push_test_case(test_case=test_case)


def pop_test_case(manager: TestCasesManager = TEST_CASES) -> \
        testtools.TestCase:
    return manager.pop_test_case()


def get_test_case(manager: TestCasesManager = TEST_CASES) -> \
        testtools.TestCase:
    return manager.get_test_case()


class DummyTestCase(TestCase):

    def runTest(self):
        pass


DUMMY_TEST_CASE = DummyTestCase()


def run_test(test_case: testtools.TestCase,
             test_result: testtools.TestResult = None) -> testtools.TestResult:
    test_result = test_result or testtools.TestResult()
    test_case.run(test_result)
    return test_result


def assert_in(needle, haystack, message: typing.Optional[str] = None,
              manager: TestCasesManager = TEST_CASES):
    get_test_case(manager=manager).assertIn(needle, haystack, message)


def get_skipped_test_cases(test_result: testtools.TestResult,
                           skip_reason: typing.Optional[str] = None):
    if skip_reason is not None:
        assert_in(skip_reason, test_result.skip_reasons)
        return test_result.skip_reasons[skip_reason]
    else:
        skipped_test_cases = list()
        for cases in test_result.skip_reasons.values():
            skipped_test_cases.extend(cases)
        return skipped_test_cases


def assert_test_case_was_skipped(test_case: testtools.TestCase,
                                 test_result: testtools.TestResult,
                                 skip_reason: str = None,
                                 manager: TestCasesManager = TEST_CASES):
    skipped_tests = get_skipped_test_cases(test_result=test_result,
                                           skip_reason=skip_reason)
    assert_in(test_case, skipped_tests, manager=manager)
