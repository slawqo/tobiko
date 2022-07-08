# Copyright (c) 2021 Red Hat, Inc.
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

import functools

from oslo_log import log

import tobiko
from tobiko.shell.sh import _exception
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _hostname
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


class CommandNotFound(tobiko.ObjectNotFound):
    message = "Command {command!r} not found on host {hostname!r}"


class SkipOnCommandNotFound(CommandNotFound, tobiko.SkipException):
    pass


@functools.lru_cache()
def find_command(command: str,
                 ssh_client: ssh.SSHClientType = None,
                 sudo=False,
                 skip=False) -> str:
    hostname = _hostname.get_hostname(ssh_client=ssh_client)
    try:
        result = _execute.execute(['which', command],
                                  ssh_client=ssh_client,
                                  sudo=sudo)
    except _exception.ShellCommandFailed as ex:
        if skip:
            raise SkipOnCommandNotFound(command=command,
                                        hostname=hostname) from ex
        else:
            raise CommandNotFound(command=command,
                                  hostname=hostname) from ex
    else:
        command_path = result.stdout.strip()
        LOG.debug(f"Command {command!r} found on host {hostname}: "
                  f"{command_path}")
        return command_path
