# Copyright 2020 Red Hat
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

from tobiko.common import _fixture


class TobikoConfigFicture(_fixture.SharedFixture):

    config = None

    def setup_fixture(self):
        from tobiko import config
        self.config = config.CONF.tobiko


def tobiko_config():
    return _fixture.setup_fixture(TobikoConfigFicture).config


def tobiko_config_dir():
    return tobiko_config().config_dir


def tobiko_config_path(path):
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(tobiko_config_dir(), path)
    return os.path.realpath(path)
