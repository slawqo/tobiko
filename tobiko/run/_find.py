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

import os
import subprocess
import sys
import typing

from oslo_log import log

from tobiko.run import _config


LOG = log.getLogger(__name__)


def find_test_files(test_path: typing.Union[str, typing.Iterable[str]] = None,
                    test_filename: str = None,
                    config: _config.RunConfigFixture = None) \
        -> typing.List[str]:
    config = _config.run_confing(config)
    if test_path is None:
        test_path = config.test_path
    elif isinstance(test_path, str):
        test_path = [test_path]
    else:
        test_path = list(test_path)
    if not test_filename:
        test_filename = config.test_filename
    test_files: typing.List[str] = []
    for path in test_path:
        path = os.path.realpath(path)
        if os.path.isfile(path):
            test_files.append(path)
            LOG.debug("Found test file:\n"
                      f"  {path}\n",)
            continue
        if os.path.isdir(path):
            find_dir = path
            find_name = test_filename
        else:
            find_dir = os.path.dirname(path)
            find_name = os.path.basename(path)

        LOG.debug("Find test files...\n"
                  f"  dir: '{find_dir}'\n"
                  f"  name: '{find_name}'")
        try:
            output = subprocess.check_output(
                ['find', find_dir, '-name', find_name],
                universal_newlines=True)
        except subprocess.CalledProcessError as ex:
            LOG.exception("Test files not found.")
            raise FileNotFoundError('Test files not found: \n'
                                    f"  dir: '{find_dir}'\n"
                                    f"  name: '{find_name}'") from ex

        for line in output.splitlines():
            line = line.strip()
            if line:
                test_files.append(line)

        LOG.debug("Found test file(s):\n"
                  "  %s", '  \n'.join(test_files))
    return test_files


def main(test_path: typing.List[str] = None):
    if test_path is None:
        test_path = sys.argv[1:]
    try:
        test_files = find_test_files(test_path=test_path)
    except Exception as ex:
        sys.stderr.write(f'{ex}\n')
        sys.exit(1)
    else:
        output = ''.join(f'{test_file}\n'
                         for test_file in test_files)
        sys.stdout.write(output)
        sys.exit(0)


if __name__ == '__main__':
    main()
