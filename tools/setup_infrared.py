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
    add_tobiko_plugin()
    ensure_workspace()
    copy_inventory()


def setup_logging(level=logging.DEBUG):
    logging.basicConfig(
        level=level,
        stream=sys.stderr,
        format='%(name)-s: %(levelname)-7s %(asctime)-15s | %(message)s')


def add_tobiko_plugin(path=None):
    path = path or os.environ.get('IR_TOBIKO_PLUGIN')
    if path:
        add_plugin('tobiko', path)


def add_plugin(name, path):
    path = normalize_path(path)
    if not os.path.isdir(path):
        message = ("invalid plug-in '{}' directory: '{}'").format(name, path)
        raise RuntimeError(message)

    remove_plugin(name)
    execute('ir plugin add "{}"', path)
    LOG.info("plug-in '%s' added from path '%s'", name, path)


def remove_plugin(name):
    try:
        execute('ir plugin remove "{}"', name)
    except subprocess.CalledProcessError as ex:
        LOG.debug("plug-in '%s' not removed: %s", name, ex)
        return False
    else:
        LOG.info("plug-in '%s' removed", name)
        return True


def ensure_workspace(filename=None):
    filename = (filename or
                os.environ.get('IR_WORKSPACE_FILE') or
                'workspace.tgz')
    filename = normalize_path(filename)
    workspace = name_from_path(filename)
    if os.path.isfile(filename):
        try:
            execute('ir workspace import "{}"', filename)
        except subprocess.CalledProcessError as ex:
            LOG.debug("workspace file '%s' not imported: %s", filename, ex)
        else:
            LOG.info("workspace imported from file '%s'", filename)
            return
    else:
        LOG.debug("workspace file not found: '%s'", filename)

    try:
        execute('ir workspace checkout "{}"', workspace)
    except subprocess.CalledProcessError as ex:
        LOG.debug("workspace '%s' not checked out: %s", workspace, ex)
    else:
        LOG.info("workspace '%s' checked out", workspace)
        return

    execute('infrared workspace checkout --create "{}"', workspace)
    LOG.info("workspace '%s' created", workspace)


def copy_inventory(filename=None):
    filename = (filename or
                os.environ.get('ANSIBLE_INVENTORY') or
                'ansible_hosts')
    if not os.path.isfile(filename):
        LOG.debug('inventary file not found: %r', filename)
        return False

    dest_file = execute('ir workspace inventory')
    LOG.debug("got workspace inventory file: '%s'", dest_file)

    dest_dir = os.path.basename(dest_file)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        LOG.info("directory created: '%s'", dest_dir)

    execute('cp {} {}', filename, dest_file)
    LOG.info("inventary file '%s' copied to '%s'", filename, dest_file)
    return True


def normalize_path(path):
    return os.path.realpath(os.path.expanduser(path))


def execute(command, *args, **kwargs):
    if args or kwargs:
        command = command.format(*args, **kwargs)
    LOG.debug("execute command: '%s'", command)
    return subprocess.check_output(command, shell=True,
                                   universal_newlines=True)


def name_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


if __name__ == '__main__':
    LOG = logging.getLogger(name_from_path(__file__))
    main()
