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
              result: unittest.TestResult = None):
    test_ids = _discover.find_test_ids(test_path=test_path,
                                       test_filename=test_filename,
                                       python_path=python_path,
                                       config=config)
    return run_test_ids(test_ids=test_ids, result=result)


def run_test_ids(test_ids: typing.List[str],
                 result: unittest.TestResult = None) \
        -> int:
    test_classes: typing.Dict[str, typing.List[str]] = \
        collections.defaultdict(list)
    # run the test suite
    if result is None:
        result = unittest.TestResult()

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
    suite.run(result)
    LOG.info(f'{result.testsRun} test(s) run')
    if result.testsRun and (result.errors or result.failures):
        raise RunTestCasesFailed(
            errors='\n'.join(str(e) for e in result.errors),
            failures='\n'.join(str(e) for e in result.failures))
    return result.testsRun


class RunTestCasesFailed(tobiko.TobikoException):
    message = ('Test case execution failed:\n'
               '{errors}\n'
               '{failures}\n')


def main(test_path: typing.Iterable[str] = None,
         test_filename: str = None,
         python_path: typing.Iterable[str] = None):
    if test_path is None:
        test_path = sys.argv[1:]
    try:
        run_tests(test_path=test_path,
                  test_filename=test_filename,
                  python_path=python_path)
    except Exception:
        LOG.exception("Error running test cases")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
