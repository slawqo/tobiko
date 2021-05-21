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
import sys

TOP_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

if TOP_DIR not in sys.path:
    sys.path.insert(0, TOP_DIR)

from tools import common  # noqa
from tools import install  # noqa


LOG = common.get_logger(__name__)


def main():
    common.setup_logging()
    ensure_podman1()


def ensure_podman1():
    try:
        import podman1
    except ImportError:
        install.install_podman1()


if __name__ == '__main__':
    main()
