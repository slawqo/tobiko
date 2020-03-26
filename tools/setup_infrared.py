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
import subprocess
import sys


LOG = logging.getLogger(__name__)


def main():
    setup_logging()
    add_plugin('tobiko', os.environ.get('IR_TOBIKO_PLUGIN'))
    import_workspace(os.environ.get('IR_WORKSPACE_FILE'))


def setup_logging(level=logging.DEBUG):
    logging.basicConfig(
        level=level, stream=sys.stderr,
        format='%(name)-s: %(levelname)-7s %(asctime)-15s | %(message)s')


def add_plugin(name, path):
    path = path or os.environ.get('IR_TOBIKO_PLUGIN')
    if path:
        path = normalize_path(path)
        if os.path.isdir(path):
            remove_plugin(name)
            execute('ir plugin add "{}"', path)


def remove_plugin(name):
    try:
        execute('ir plugin remove "{}"', name)
    except subprocess.CalledProcessError:
        return False
    else:
        return True


def import_workspace(filename):
    if filename:
        filename = normalize_path(filename)
        if os.path.isfile(filename):
            try:
                execute('ir workspace import "{}"', filename)
            except subprocess.CalledProcessError:
                # If file was already imported before we checkout to its
                # workspace
                workspace = name_from_path(filename)
                execute('ir workspace checkout "{}"', workspace)


def normalize_path(path):
    return os.path.realpath(os.path.expanduser(path))


def execute(command, *args, **kwargs):
    if args or kwargs:
        command = command.format(*args, **kwargs)
    LOG.info('%s', command)
    return subprocess.check_output(command, shell=True)


def name_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


if __name__ == '__main__':
    LOG = logging.getLogger(name_from_path(__file__))
    main()
