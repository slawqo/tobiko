#!/usr/bin/env python3
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

import os
import site
import sys
import typing


TOP_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

if TOP_DIR not in sys.path:
    sys.path.insert(0, TOP_DIR)

from tools import common  # noqa
from tools import get_version  # noqa

LOG = common.get_logger(__name__)

TOX_VERSION = os.environ.get('TOX_VERSION') or '>=3.8.0'

TOX_CONSTRAINTS_FILE = (
    os.environ.get('TOX_CONSTRAINTS_FILE') or
    'https://opendev.org/openstack/requirements/raw/branch/master/upper-constraints.txt')

TOX_CONSTRAINTS = (
    os.environ.get('TOX_CONSTRAINTS') or f"'-c{TOX_CONSTRAINTS_FILE}'")


def main():
    common.setup_logging()
    install_tox()
    install_bindeps()
    install_podman1()
    install_tobiko()


def install_tox(version=TOX_VERSION):
    LOG.info(f"Installing Tox... (version: {version})")
    pip_install(f"'tox{version}'")


def install_bindeps():
    LOG.info(f"Installing Tobiko binary dependencies...")
    common.execute(os.path.join(TOP_DIR, 'tools', 'install-bindeps.sh'),
                   capture_stdout=False)


def install_tobiko():
    version = get_version.get_version()
    LOG.info(f"Installing Tobiko version {version}...")
    pip_install(f"-e '{TOP_DIR}'")


def install_podman1(version='===1.6.0'):
    pip_unisntall('podman')

    LOG.info(f"Installing Podman... (version: {version})")

    site_dirs = {os.path.dirname(os.path.realpath(site_dir))
                 for site_dir in site.getsitepackages()
                 if os.path.isdir(site_dir)}
    more_site_dirs = {os.path.join(site_dir, 'site-packages')
                      for site_dir in site_dirs
                      if os.path.isdir(os.path.join(site_dir, 'site-packages'))}
    site_dirs.update(more_site_dirs)
    LOG.debug(f"Site packages dirs: {site_dirs}")

    # Must ensure pre-existing podman directories are restored
    # after installation
    podman_dirs = [os.path.join(site_dir, 'podman')
                   for site_dir in sorted(site_dirs)]
    LOG.debug(f"Possible podman directories: {podman_dirs}")
    with common.stash_dir(*podman_dirs):
        for podman_dir in podman_dirs:
            assert not os.path.exists(podman_dir)
        pip_install(f"'podman{version}'")
        for podman_dir in podman_dirs:
            if os.path.isdir(podman_dir):
                # Rename podman directory to podman1
                os.rename(podman_dir, podman_dir + '1')
                break
        else:
            raise RuntimeError("Podman directory not found!")
        for podman_dir in podman_dirs:
            assert not os.path.exists(podman_dir)


def pip_install(args):
    LOG.debug(f"Installing packages: {args}...")
    common.execute_python(f"-m pip install {TOX_CONSTRAINTS} {args}",
                          capture_stdout=False)


def pip_unisntall(args):
    LOG.debug(f"Uninstalling packages: {args}...")
    common.execute_python(f"-m pip uninstall -y {args}",
                          capture_stdout=False)


if __name__ == '__main__':
    main()
