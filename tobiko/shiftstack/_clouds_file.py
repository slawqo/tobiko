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

import os.path

import tobiko
from tobiko.shell import sh
from tobiko import tripleo


class ShiftStackCloudsFileFixture(tobiko.SharedFixture):

    def __init__(self,
                 local_clouds_file_path: str = None,
                 remote_clouds_file_path: str = None,
                 connection: sh.ShellConnection = None):
        super(ShiftStackCloudsFileFixture, self).__init__()
        self._local_clouds_file_path = local_clouds_file_path
        self._remote_clouds_file_path = remote_clouds_file_path
        self._connection = connection

    @property
    def local_clouds_file_path(self) -> str:
        if self._local_clouds_file_path is None:
            self._local_clouds_file_path = tobiko.tobiko_config_path(
                tobiko.tobiko_config().shiftstack.local_clouds_file_path)
        assert isinstance(self._local_clouds_file_path, str)
        return self._local_clouds_file_path

    @property
    def remote_clouds_file_path(self) -> str:
        if self._remote_clouds_file_path is None:
            self._remote_clouds_file_path = (
                tobiko.tobiko_config().shiftstack.remote_clouds_file_path)
        assert isinstance(self._remote_clouds_file_path, str)
        return self._remote_clouds_file_path

    @property
    def connection(self) -> sh.ShellConnection:
        if self._connection is None:
            self._connection = sh.shell_connection(
                tripleo.undercloud_ssh_client())
        assert isinstance(self._connection, sh.ShellConnection)
        return self._connection

    def setup_fixture(self):
        tobiko.makedirs(os.path.dirname(self.local_clouds_file_path),
                        exist_ok=True)
        self.connection.get_file(
            remote_file=self.remote_clouds_file_path,
            local_file=self.local_clouds_file_path)


def get_clouds_file_path() -> str:
    return tobiko.setup_fixture(
        ShiftStackCloudsFileFixture).local_clouds_file_path
