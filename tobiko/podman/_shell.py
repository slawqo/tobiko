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

from tobiko.podman import _exception
from tobiko.shell import sh


def discover_podman_socket(ssh_client=None, **execute_params):
    cmd = "systemctl list-sockets | grep podman | awk '{print $1}'"
    result = sh.execute(cmd, stdin=False, stdout=True, stderr=True,
                        expect_exit_status=None, ssh_client=ssh_client,
                        **execute_params)
    if result.exit_status or not result.stdout:
        raise _exception.PodmanSocketNotFoundError(details=result.stderr)
    try:
        socket = result.stdout.splitlines()[0]
    except IndexError as ex:
        podman_error = _exception.PodmanSocketNotFoundError(
            details=result.stderr)
        raise podman_error from ex
    if '0 sockets listed' in socket:
        raise _exception.PodmanSocketNotFoundError(details=socket)
    return socket


def is_podman_running(ssh_client=None, **execute_params):
    try:
        discover_podman_socket(ssh_client=ssh_client, **execute_params)
    except _exception.PodmanSocketNotFoundError:
        return False
    else:
        return True
