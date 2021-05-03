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

import argparse
import json
import logging
import os
import subprocess
import sys


LOG = logging.getLogger(__name__)

GET_PYTHON_VERSION_SCRIPT = """
import sys

version = '.'.join(str(i) for i in sys.version_info)
print(version)
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--quiet', '-q',
                        action="store_true",
                        help="mute logging messages from STDERR")
    parser.add_argument('--base', '-b',
                        action="store_true",
                        help="print Python base prefix")
    args = parser.parse_args()

    setup_logging(quiet=args.quiet)
    version = get_python_version()
    executables = [
        info['executable']
        for info in iter_python_executables_info(match_version=version,
                                                 base=args.base)]
    info = {'version': version,
            'executable': sys.executable,
            'executables': executables}
    output = json.dumps(info)
    assert output.startswith('{')
    print(output)


def setup_logging(quiet=False):
    if quiet:
        level = logging.ERROR
    else:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format='%(name)-s: %(levelname)-7s %(asctime)-15s | %(message)s')


def get_python_version():
    return '.'.join(str(i) for i in sys.version_info)


def iter_python_executables_info(match_version=None, base=None):
    last_error = None
    for executable in iter_python_executables(base=base):
        command = subprocess.list2cmdline(
            [executable, '-c', GET_PYTHON_VERSION_SCRIPT])
        try:
            version = execute(command).splitlines()[0]
        except subprocess.CalledProcessError:
            LOG.exception('Unable to get version from script')
        else:
            if not match_version or match_version == version:
                yield {'executable': executable, 'version': version}
    else:
        if last_error:
            raise last_error


def iter_python_executables(base):
    if base:
        prefix = getattr(sys, 'base_prefix', sys.prefix)
    else:
        prefix = sys.prefix
    if prefix:
        if os.path.isdir(prefix):
            for python_name in iter_versioned_names():
                executable = os.path.join(prefix, 'bin', python_name)
                if os.path.isfile(executable):
                    yield executable


def iter_versioned_names(unversioned=None):
    unversioned = unversioned or 'python'
    short_versioned = unversioned + str(sys.version_info[0])
    long_versioned = '.'.join([short_versioned, str(sys.version_info[1])])
    yield long_versioned
    yield short_versioned
    yield unversioned


def execute(command, *args, **kwargs):
    if args or kwargs:
        command = command.format(*args, **kwargs)
    LOG.debug('%s', command)
    env = kwargs.get('env', None)
    return subprocess.check_output(command, shell=True,
                                   universal_newlines=True,
                                   env=env)


def name_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


if __name__ == '__main__':
    LOG = logging.getLogger(name_from_path(__file__))
    main()
