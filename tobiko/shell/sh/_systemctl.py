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

import collections
import re
import typing

from oslo_log import log

import tobiko
from tobiko.shell.sh import _command
from tobiko.shell.sh import _execute
from tobiko.shell import ssh

# pylint: disable=redefined-builtin

LOG = log.getLogger(__name__)


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
        message = line.strip()
        if not message:
            # Legend is coming after the first empty line
            break

        if message == '0 loaded units listed.':
            raise SystemdUnitNotFound(command=command, output=output)

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


def wait_for_active_systemd_units(*pattern: str,
                                  state: str = None,
                                  type: str = None,
                                  timeout: tobiko.Seconds = None,
                                  interval: tobiko.Seconds = None,
                                  ssh_client: ssh.SSHClientType = None,
                                  sudo: bool = None) \
        -> tobiko.Selection[SystemdUnit]:
    return wait_for_systemd_units_state(match_unit_state(active='ACTIVE'),
                                        *pattern,
                                        state=state,
                                        type=type,
                                        timeout=timeout,
                                        interval=interval,
                                        ssh_client=ssh_client,
                                        sudo=sudo)


MATCH_ALL = re.compile(r'.*')
Pattern = type(MATCH_ALL)
PatternType = typing.Union[str, typing.Pattern[str]]


def compile_pattern(pattern: typing.Optional[PatternType]) \
        -> typing.Pattern[str]:
    if pattern is None:
        return MATCH_ALL
    elif isinstance(pattern, str):
        return re.compile(pattern, re.IGNORECASE)
    tobiko.check_valid_type(pattern, Pattern)
    return pattern


class MatchUnitState(typing.NamedTuple):
    load: typing.Pattern[str] = MATCH_ALL
    active: typing.Pattern[str] = MATCH_ALL
    sub: typing.Pattern[str] = MATCH_ALL

    def match_unit(self, unit: SystemdUnit) -> bool:
        return bool(self.load.match(unit.load) and
                    self.active.match(unit.active) and
                    self.sub.match(unit.sub))

    def __call__(self, unit: SystemdUnit) -> bool:
        return self.match_unit(unit)

    def __repr__(self) -> str:
        details = []
        if self.load != MATCH_ALL:
            details.append(f"load={self.load.pattern!r}")
        if self.active != MATCH_ALL:
            details.append(f"load={self.active.pattern!r}")
        if self.sub != MATCH_ALL:
            details.append(f"load={self.sub.pattern!r}")
        details_text = ', '.join(details)
        return f'{type(self).__name__}({details_text})'


def match_unit_state(load: PatternType = None,
                     active: PatternType = None,
                     sub: PatternType = None) \
        -> typing.Callable[[SystemdUnit], bool]:
    return typing.cast(
        typing.Callable[[SystemdUnit], bool],
        MatchUnitState(load=compile_pattern(load),
                       active=compile_pattern(active),
                       sub=compile_pattern(sub)))


def wait_for_systemd_units_state(
        match_unit: typing.Callable[[SystemdUnit], bool],
        *pattern: str,
        state: str = None,
        type: str = None,
        ssh_client: ssh.SSHClientType = None,
        sudo: bool = None,
        check: bool = True,
        timeout: tobiko.Seconds = None,
        interval: tobiko.Seconds = None) \
        -> tobiko.Selection[SystemdUnit]:
    all_units: typing.Dict[str, SystemdUnit] = collections.OrderedDict()
    bad_units = tobiko.Selection[SystemdUnit]()
    for attempt in tobiko.retry(timeout=timeout,
                                interval=interval,
                                default_timeout=30.,
                                default_interval=5.):
        units = list_systemd_units(*pattern,
                                   all=True,
                                   state=state,
                                   type=type,
                                   ssh_client=ssh_client,
                                   sudo=sudo)
        assert units
        all_units.update((unit.unit, unit) for unit in units)

        bad_units = units.select(match_unit, expect=False)
        if not bad_units:
            break

        LOG.info('Systemd unit(s) still on unexpected state:'
                 f' expected: ({match_unit})...:\n'
                 '  actual: \n'
                 '\n'.join(f'    - {u}' for u in bad_units))
        if attempt.is_last:
            break
        pattern = tuple(u.unit for u in bad_units)

    if check:
        if bad_units:
            raise UnexpectedSystemctlUnitState(matcher=match_unit,
                                               units=bad_units)
    return tobiko.Selection(all_units.values())


class SystemdUnitNotFound(tobiko.TobikoException):
    message = ("Systemd unit(s) not found\n"
               "  command: {command}\n"
               "  output: {output}")


class UnexpectedSystemctlUnitState(tobiko.TobikoException):
    message = ("Systemd unit(s) has unexpected state: \n"
               "  expected: {matcher}\n"
               "  actual: {units}")
