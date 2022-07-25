# Copyright (c) 2021 Red Hat, Inc.
#
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

import collections
import sys
import typing
import unittest

from oslo_log import log

import tobiko
from tobiko.run import _config
from tobiko.run import _discover


LOG = log.getLogger(__name__)


def run_tests(test_path: typing.Union[str, typing.Iterable[str]],
              test_filename: str = None,
              python_path: typing.Iterable[str] = None,
              config: _config.RunConfigFixture = None,
              result: unittest.TestResult = None,
              check=True) -> unittest.TestResult:
    test_ids = _discover.find_test_ids(test_path=test_path,
                                       test_filename=test_filename,
                                       python_path=python_path,
                                       config=config)
    return run_test_ids(test_ids=test_ids, result=result, check=check)


def run_test_ids(test_ids: typing.List[str],
                 result: unittest.TestResult = None,
                 check=True) \
        -> unittest.TestResult:
    test_classes: typing.Dict[str, typing.List[str]] = \
        collections.defaultdict(list)

    # regroup test ids my test class keeping test names order
    test_ids = list(test_ids)
    for test_id in test_ids:
        test_class_id, test_name = test_id.rsplit('.', 1)
        test_classes[test_class_id].append(test_name)

    # add test cases to the suite ordered by class name
    suite = unittest.TestSuite()
    for test_class_id, test_names in sorted(test_classes.items()):
        test_class = tobiko.load_object(test_class_id)
        for test_name in test_names:
            test = test_class(test_name)
            suite.addTest(test)

    LOG.info(f'Run {len(test_ids)} test(s)')
    result = tobiko.run_test(case=suite, result=result, check=check)

    LOG.info(f'{result.testsRun} test(s) run')
    return result


class RunTestCasesFailed(tobiko.TobikoException):
    message = ('Test case execution failed:\n'
               '{errors}\n'
               '{failures}\n')


def main(test_path: typing.Iterable[str] = None,
         test_filename: str = None,
         python_path: typing.Iterable[str] = None):
    if test_path is None:
        test_path = sys.argv[1:]

    result = run_tests(test_path=test_path,
                       test_filename=test_filename,
                       python_path=python_path)

    for case, exc_info in result.errors:
        LOG.exception(f"Test case error: {case.id()}",
                      exc_info=exc_info)

    for case, exc_info in result.errors:
        LOG.exception(f"Test case failure: {case.id()}",
                      exc_info=exc_info)

    for case, reason in result.skipped:
        LOG.info(f"Test case skipped: {case.id()} ({reason})")

    LOG.info(f"{result.testsRun} test case(s) executed:\n"
             f"  errors:   {len(result.errors)}"
             f"  failures: {len(result.failures)}"
             f"  skipped:  {len(result.skipped)}")
    if result.errors or result.failures:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
