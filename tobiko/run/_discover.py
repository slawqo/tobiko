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

import inspect
import os
import sys
import typing
import unittest

from oslo_log import log

import tobiko
from tobiko.run import _config
from tobiko.run import _find
from tobiko.run import _worker


LOG = log.getLogger(__name__)


def find_test_ids(test_path: typing.Union[str, typing.Iterable[str]],
                  test_filename: str = None,
                  python_path: typing.Iterable[str] = None,
                  forked: bool = None,
                  config: _config.RunConfigFixture = None) \
        -> typing.List[str]:
    config = _config.run_confing(config)
    test_files = _find.find_test_files(test_path=test_path,
                                       test_filename=test_filename,
                                       config=config)
    if not python_path:
        python_path = config.python_path
    if forked is None:
        forked = bool(config.forked)

    if forked:
        return forked_discover_test_ids(test_files=test_files,
                                        python_path=python_path)
    else:
        return discover_test_ids(test_files=test_files,
                                 python_path=python_path)


def discover_test_ids(test_files: typing.Iterable[str],
                      python_path: typing.Iterable[str] = None) \
        -> typing.List[str]:
    if not python_path:
        python_path = sys.path
    python_dirs = [os.path.realpath(p) + '/'
                   for p in python_path
                   if os.path.isdir(p)]
    test_ids: typing.List[str] = []
    for test_file in test_files:
        test_ids.extend(discover_file_test_ids(test_file=test_file,
                                               python_dirs=python_dirs))
    return test_ids


def discover_file_test_ids(test_file: str,
                           python_dirs: typing.Iterable[str]) \
        -> typing.List[str]:
    test_file = os.path.realpath(test_file)
    if not os.path.isfile(test_file):
        raise ValueError(f"Test file doesn't exist: '{test_file}'")

    if not test_file.endswith('.py'):
        raise ValueError(f"Test file hasn't .py suffix: '{test_file}'")

    for python_dir in python_dirs:
        if test_file.startswith(python_dir):
            module_name = test_file[len(python_dir):-3].replace('/', '.')
            return discover_module_test_ids(module_name)

    raise ValueError(f"Test file not in Python path: '{test_file}'")


def discover_module_test_ids(module_name: str) -> typing.List[str]:
    LOG.debug(f"Load test module '{module_name}'...")
    module = tobiko.load_module(module_name)
    test_file = module.__file__
    LOG.debug("Inspect test module:\n"
              f"  module: '{module_name}'\n"
              f"  filename: '{test_file}'\n")
    test_ids: typing.List[str] = []
    for obj_name in dir(module):
        try:
            obj = getattr(module, obj_name)
        except AttributeError:
            LOG.warning("Error getting object "
                        f"'{module_name}.{obj_name}'",
                        exc_info=1)
            continue
        if (inspect.isclass(obj) and
                issubclass(obj, unittest.TestCase) and
                not inspect.isabstract(obj)):
            LOG.debug("Inspect test class members...\n"
                      f"  file: '{test_file}'\n"
                      f"  module: '{module_name}'\n"
                      f"  object: '{obj_name}'\n")
            for member_name in dir(obj):
                if member_name.startswith('test_'):
                    member_id = f"{module_name}.{obj_name}.{member_name}"
                    try:
                        member = getattr(obj, member_name)
                    except Exception:
                        LOG.error(f'Error getting "{member_id}"', exc_info=1)
                        continue
                    if not callable(member):
                        LOG.error("Class member is not callable: "
                                  f"'{member_id}'")
                        continue
                    test_ids.append(member_id)
    return test_ids


def forked_discover_test_ids(test_files: typing.Iterable[str],
                             python_path: typing.Iterable[str] = None) \
        -> typing.List[str]:
    results = [_worker.call_async(discover_test_ids,
                                  test_files=[test_file],
                                  python_path=python_path)
               for test_file in test_files]
    test_ids: typing.List[str] = []
    for result in results:
        test_ids.extend(result.get())
    return test_ids


def main(test_path: typing.Iterable[str] = None,
         test_filename: str = None,
         forked: bool = None,
         python_path: typing.Iterable[str] = None):
    if test_path is None:
        test_path = sys.argv[1:]
    try:
        test_ids = find_test_ids(test_path=test_path,
                                 test_filename=test_filename,
                                 forked=forked,
                                 python_path=python_path)
    except Exception as ex:
        sys.stderr.write(f'{ex}\n')
        sys.exit(1)
    else:
        output = ''.join(f'{test_id}\n'
                         for test_id in test_ids)
        sys.stdout.write(output)
        sys.exit(0)


if __name__ == '__main__':
    main()
