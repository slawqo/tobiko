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
from tobiko.run import _worker


LOG = log.getLogger(__name__)


def run_tests(test_path: typing.Iterable[str],
              test_filename: str = None,
              python_path: typing.Iterable[str] = None,
              forked: bool = None,
              config: _config.RunConfigFixture = None):
    test_ids = _discover.find_test_ids(test_path=test_path,
                                       test_filename=test_filename,
                                       python_path=python_path,
                                       forked=forked,
                                       config=config)
    if forked:
        forked_run_test_ids(test_ids=test_ids)
    else:
        run_test_ids(test_ids=test_ids)


def run_test_ids(test_ids: typing.Iterable[str]) -> int:
    test_classes: typing.Dict[str, typing.List[str]] = \
        collections.defaultdict(list)
    test_ids = list(test_ids)
    LOG.info(f'Run {len(test_ids)} test(s)')
    for test_id in test_ids:
        test_class_id, test_name = test_id.rsplit('.', 1)
        test_classes[test_class_id].append(test_name)
    result = unittest.TestResult()
    for test_class_id, test_names in sorted(test_classes.items()):
        LOG.info(f'Enter test class {test_class_id}')
        test_class = tobiko.load_object(test_class_id)
        for test_name in test_names:
            LOG.info(f'Enter test case {test_class_id}.{test_name}')
            test_case = test_class(test_name)
            test_case.run(result)
            LOG.info(f'Exit test case {test_class_id}.{test_name}')
        LOG.info(f'Exit test class {test_class_id}')
    LOG.info(f'{result.testsRun} test(s) run')
    return result.testsRun


def forked_run_test_ids(test_ids: typing.Iterable[str]) -> int:
    test_classes: typing.Dict[str, typing.List[str]] = \
        collections.defaultdict(list)
    test_ids = list(test_ids)
    LOG.info(f'Run {len(test_ids)} test(s)')
    for test_id in test_ids:
        test_class_id, _ = test_id.rsplit('.', 1)
        test_classes[test_class_id].append(test_id)
    results = [_worker.call_async(run_test_ids, test_ids=grouped_ids)
               for _, grouped_ids in sorted(test_classes.items())]
    count = 0
    for result in results:
        count += result.get()
    LOG.info(f'{count} test(s) run')
    return count


def main(test_path: typing.Iterable[str] = None,
         test_filename: str = None,
         forked: bool = True,
         python_path: typing.Iterable[str] = None):
    if test_path is None:
        test_path = sys.argv[1:]
    try:
        run_tests(test_path=test_path,
                  test_filename=test_filename,
                  forked=forked,
                  python_path=python_path)
    except Exception as ex:
        sys.stderr.write(f'{ex}\n')
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
