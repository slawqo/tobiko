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
from tobiko.shell.sh import _execute


class HostnameError(tobiko.TobikoException):
    message = "Unable to get hostname from host: {error}"


def get_hostname(ssh_client=None, **execute_params):
    if ssh_client is False:
        return socket.gethostname()
    else:
        result = _execute.execute('hostname', stdin=False, stdout=True,
                                  stderr=True, expect_exit_status=None,
                                  ssh_client=ssh_client, **execute_params)
        if result.exit_status or not result.stdout:
            raise HostnameError(error=result.stderr)
        return result.stdout.splitlines()[0].strip()
