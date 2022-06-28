# Copyright 2022 Red Hat
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

from oslo_log import log

import tobiko
from tobiko.shell import sh


LOG = log.getLogger(__name__)


class KeyFileFixture(tobiko.SharedFixture):

    def __init__(self,
                 key_file: str = None,
                 key_type: str = None):
        super(KeyFileFixture, self).__init__()
        if key_file is None:
            key_file = tobiko.tobiko_config().nova.key_file
        self.key_file = tobiko.tobiko_config_path(key_file)
        if key_type is None:
            key_type = tobiko.tobiko_config().nova.key_type
        self.key_type = key_type

    def setup_fixture(self):
        self.ensure_key_file()

    def ensure_key_file(self):
        key_file = tobiko.check_valid_type(self.key_file, str)
        LOG.debug(f'Ensuring Nova key files exist: {key_file}')
        if os.path.isfile(key_file):
            if os.path.isfile(f'{key_file}.pub'):
                LOG.info(f"Key file found: {key_file}")
                return
            else:
                LOG.info(f"Public key file not found: {key_file}.pub")
        else:
            LOG.info(f"Key file not found: {key_file}")

        LOG.info(f"Creating file for key pairs: '{self.key_file}'...")
        key_dir = os.path.dirname(key_file)
        tobiko.makedirs(key_dir)
        try:
            sh.local_execute(['ssh-keygen',
                              '-f', key_file,
                              '-P', '',
                              '-t', self.key_type])
        except sh.ShellCommandFailed:
            if (not os.path.isfile(key_file) or
                    not os.path.isfile(key_file + '.pub')):
                raise
        else:
            assert os.path.isfile(key_file)
            assert os.path.isfile(key_file + '.pub')
            LOG.info(f'Key file created: {self.key_file}')


def get_key_file() -> str:
    return tobiko.setup_fixture(KeyFileFixture).key_file
