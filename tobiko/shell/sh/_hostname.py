# Copyright (c) 2019 Red Hat, Inc.
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

import socket

import tobiko
from tobiko.shell.sh import _exception
from tobiko.shell.sh import _execute
from tobiko.shell import ssh


class HostnameError(tobiko.TobikoException):
    message = "Unable to get hostname from host: {error}"


def get_hostname(ssh_client: ssh.SSHClientType = None,
                 **execute_params) -> str:
    if ssh_client is False:
        return socket.gethostname()

    tobiko.check_valid_type(ssh_client, ssh.SSHClientFixture,
                            type(None))
    try:
        result = _execute.execute('hostname',
                                  ssh_client=ssh_client,
                                  **execute_params)
    except _exception.ShellCommandFailed as ex:
        raise HostnameError(error=ex.stderr) from ex

    line: str
    for line in result.stdout.splitlines():
        hostname = line.strip()
        if hostname:
            break
    else:
        raise HostnameError(error=f"Invalid result: '{result}'")

    return hostname
