# Copyright (c) 2020 Red Hat, Inc.
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
import typing

from oslo_log import log

import tobiko
from tobiko.shell.ssh import _client


LOG = log.getLogger(__name__)


DEFAULT_SSH_KEY_FILE = "~/.ssh/id_rsa"


def get_key_file(ssh_client: _client.SSHClientFixture,
                 key_file: str = DEFAULT_SSH_KEY_FILE):
    return tobiko.setup_fixture(
        GetSSHKeyFileFixture(ssh_client=ssh_client,
                             remote_key_file=key_file)).key_file


class GetSSHKeyFileFixture(tobiko.SharedFixture):

    key_file = None

    def __init__(self, ssh_client: _client.SSHClientFixture,
                 remote_key_file: str = DEFAULT_SSH_KEY_FILE):
        super(GetSSHKeyFileFixture, self).__init__()
        self.ssh_client = ssh_client
        self.remote_key_file = remote_key_file

    def setup_fixture(self):
        client = self.ssh_client.connect()
        _, stdout, stderr = client.exec_command('hostname')
        remote_hostname = stdout.read().strip().decode()
        if not remote_hostname:
            error = stderr.read()
            raise RuntimeError(
                "Unable to get hostname from proxy jump server:\n"
                f"{error}")

        _, stdout, stderr = client.exec_command(
            f"cat {self.remote_key_file}")
        private_key = stdout.read()
        if not private_key:
            error = stderr.read()
            LOG.error("Unable to get SSH private key from proxy jump "
                      f"server:\n{error}")
            return

        _, stdout, stderr = client.exec_command(
            f"cat {self.remote_key_file}.pub")
        public_key = stdout.read()
        if not public_key:
            error = stderr.read()
            LOG.error("Unable to get SSH public key from proxy jump "
                      f"server:\n{error}")
            return

        key_file = tobiko.tobiko_config_path(
            f"~/.ssh/{os.path.basename(self.remote_key_file)}-" +
            remote_hostname)
        with tobiko.open_output_file(key_file) as fd:
            fd.write(private_key.decode())
        with tobiko.open_output_file(key_file + '.pub') as fd:
            fd.write(public_key.decode())
        self.key_file = key_file


def list_key_filenames() -> typing.List[str]:
    return tobiko.setup_fixture(KeyFilenamesFixture).key_filenames


def list_proxy_jump_key_filenames() -> typing.List[str]:
    return tobiko.setup_fixture(ProxyJumpKeyFilenamesFixture).key_filenames


class KeyFilenamesFixture(tobiko.SharedFixture):

    def __init__(self):
        super().__init__()
        self.key_filenames: typing.List[str] = []

    def setup_fixture(self):
        conf = tobiko.tobiko_config()
        for key_file in tobiko.select_uniques(conf.ssh.key_file):
            if key_file:
                key_file = tobiko.tobiko_config_path(key_file)
                if (key_file not in self.key_filenames and
                        os.path.isfile(key_file)):
                    LOG.info(f"Use local keyfile: {key_file}")
                    self.key_filenames.append(key_file)


class ProxyJumpKeyFilenamesFixture(KeyFilenamesFixture):

    def setup_fixture(self):
        ssh_proxy_client = _client.ssh_proxy_client()
        if ssh_proxy_client is None:
            return

        conf = tobiko.tobiko_config()
        remote_key_files = tobiko.select_uniques(conf.ssh.key_file)
        for remote_key_file in remote_key_files:
            key_file = get_key_file(ssh_client=ssh_proxy_client,
                                    key_file=remote_key_file)
            if (key_file and
                    key_file not in self.key_filenames and
                    os.path.isfile(key_file)):
                LOG.info(f"Use SSH proxy server keyfile: {key_file}")
                self.key_filenames.append(key_file)
