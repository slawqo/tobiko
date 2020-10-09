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
import shlex
import subprocess
import sys
import tempfile


LOG = logging.getLogger(__name__)
BASH_EXECUTABLE = '/bin/bash'
PYTHON_EXECUTABLE = os.environ.get('PYTHON', sys.executable)


def get_logger(name):
    module = sys.modules.get(name)
    if module:
        name = name_from_path(module.__file__)
    return logging.getLogger(name)


def setup_logging(main_script=None, level=logging.DEBUG):
    main_script = main_script or sys.modules['__main__'].__file__
    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format='%(name)-s: %(levelname)-7s %(asctime)-15s | %(message)s')
    return logging.getLogger(name=name_from_path(main_script))


def name_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


def normalize_path(path):
    return os.path.realpath(os.path.expanduser(path))


def execute(command, *args, **kwargs):
    capture_stdout = kwargs.pop('capture_stdout', True)
    universal_newlines = kwargs.pop('universal_newlines', True)
    check = kwargs.pop('check', True)
    shell = kwargs.pop('shell', '/bin/bash')

    if args or kwargs:
        command = command.format(*args, **kwargs)
    command = command.strip()

    stdout = capture_stdout and subprocess.PIPE or None

    if shell:
        command_line = [shell, '-x', '-c', command]
    else:
        command_line = shlex.split(command)

    LOG.info(f"Execute: {command_line}")
    result = subprocess.run(command_line,
                            stdout=stdout, shell=False,
                            universal_newlines=universal_newlines)
    if check:
        result.check_returncode()
    return result.stdout


def execute_python(command, *args, **kwargs):
    capture_stdout = kwargs.pop('capture_stdout', True)
    universal_newlines = kwargs.pop('universal_newlines', True)
    check = kwargs.pop('check', True)
    interpreter = kwargs.pop('interpreter', PYTHON_EXECUTABLE)

    if args or kwargs:
        command = command.format(*args, **kwargs)
    command = command.strip()
    command_line = [interpreter] + shlex.split(command)

    stdout = capture_stdout and subprocess.PIPE or None
    LOG.info(f"Execute: {command_line}")
    result = subprocess.run(command_line,
                            stdout=stdout, shell=False,
                            universal_newlines=universal_newlines)
    if check:
        result.check_returncode()
    return result.stdout


def get_posargs(args=None):
    if args is None:
        args = sys.argv[1:]
    return ' '.join(shlex.quote(s) for s in args)


def make_temp(*args, **kwargs):
    fd, filename = tempfile.mkstemp(*args, **kwargs)
    os.close(fd)
    return filename


def make_dir(dirname):
    if os.path.isdir(dirname):
        return False
    else:
        LOG.debug("Create directory: '%s'", dirname)
        os.makedirs(dirname)
        return True


def remove_file(filename):
    if os.path.isfile(filename):
        LOG.debug("Remove file: '%s'", filename)
        os.unlink(filename)
        return True
    else:
        return False
