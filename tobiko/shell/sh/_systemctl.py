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

import re
import typing

import tobiko
from tobiko.shell.sh import _command
from tobiko.shell.sh import _execute
from tobiko.shell import ssh

# pylint: disable=redefined-builtin


class SystemdUnit(typing.NamedTuple):
    unit: str
    load: str
    active: str
    sub: str
    description: str
    data: typing.Dict[str, typing.Any]


IS_WORD_PATTERN = re.compile(r'\S+')


def systemctl_command(command: str,
                      *units: str,
                      all: bool = None,
                      no_pager: bool = None,
                      plain: bool = None,
                      state: str = None,
                      type: str = None) \
        -> _command.ShellCommand:
    command_line = _command.shell_command('systemctl') + command
    if all:
        command_line += '-a'
    if no_pager:
        command_line += '--no-pager'
    if plain:
        command_line += '--plain'
    if state is not None:
        command_line += f'"--state={state}"'
    if type is not None:
        command_line += f'-t "{type}"'
    if units:
        command_line += units
    return command_line


def list_systemd_units(*pattern: str,
                       all: bool = None,
                       state: str = None,
                       type: str = None,
                       ssh_client: ssh.SSHClientType = None,
                       sudo: bool = None) \
        -> tobiko.Selection[SystemdUnit]:
    command = systemctl_command('list-units', *pattern, all=all,
                                no_pager=True, plain=True, state=state,
                                type=type)
    output = _execute.execute(command,
                              ssh_client=ssh_client,
                              sudo=sudo).stdout
    table_lines = iter(output.splitlines())
    first_line = next(table_lines)
    search_pos = 0
    names: typing.List[str] = []
    starts: typing.List[int] = []
    while True:
        match = IS_WORD_PATTERN.search(first_line, search_pos)
        if match is None:
            break
        names.append(match.group(0).lower())
        starts.append(match.start())
        search_pos = match.end()
    ends: typing.List[int] = list(starts[1:]) + [-1]

    units = tobiko.Selection[SystemdUnit]()
    for line in table_lines:
        if not line.strip():
            # Legend is coming after the first empty line
            break
        data: typing.Dict[str, str] = {}
        for name, start, end in zip(names, starts, ends):
            data[name] = line[start:end].strip()
        units.append(SystemdUnit(unit=data.get('unit', ''),
                                 load=data.get('load', ''),
                                 active=data.get('active', ''),
                                 sub=data.get('sub', ''),
                                 description=data.get('description', ''),
                                 data=data))
    return units
