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

import re
import typing

from oslo_log import log

import tobiko
from tobiko.shell.sh import _cmdline
from tobiko.shell.sh import _command
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _hostname
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


class PsError(tobiko.TobikoException):
    message = "Unable to list processes from host: {error}"


class PsWaitTimeout(PsError):
    message = ("Process(es) still running on host {hostname!r} after "
               "{timeout} seconds:\n{processes!s}")


IS_KERNEL_RE = re.compile('^\\[.*\\]$')


_NOT_FOUND = object()


class PsProcessBase:
    command: str
    pid: int
    ssh_client: ssh.SSHClientType
    is_cirros: typing.Optional[bool] = None

    @property
    def is_kernel(self) -> bool:
        return IS_KERNEL_RE.match(self.command) is not None

    @property
    def command_line(self) -> typing.Optional[_command.ShellCommand]:
        try:
            return _cmdline.get_command_line(command=self.command,
                                             pid=self.pid,
                                             ssh_client=self.ssh_client,
                                             _cache_id=id(self))
        except _cmdline.GetCommandLineError as ex:
            LOG.error(str(ex))
            return None

    def kill(self, signal: int = None, **execute_params):
        execute_params.update(ssh_client=self.ssh_client)
        command_line = _command.shell_command("kill")
        if signal is not None:
            command_line += f"-s {signal}"
        command_line += str(self.pid)
        _execute.execute(command_line, **execute_params)

    def wait(self,
             timeout: tobiko.Seconds = None,
             sleep_interval: tobiko.Seconds = None,
             **execute_params):
        execute_params.update(ssh_client=self.ssh_client)
        wait_for_processes(timeout=timeout,
                           sleep_interval=sleep_interval,
                           is_cirros=self.is_cirros,
                           pid=self.pid,
                           **execute_params)


class PsProcessTuple(typing.NamedTuple):
    """Process listed by ps command
    """
    command: str
    pid: int
    ssh_client: ssh.SSHClientType
    is_cirros: typing.Optional[bool] = None


class PsProcess(PsProcessTuple, PsProcessBase):
    pass


P = typing.TypeVar('P', bound=PsProcessBase)


def select_processes(
        processes: typing.Iterable[PsProcessBase],
        command: str = None,
        pid: int = None,
        is_kernel: typing.Optional[bool] = False,
        command_line: _command.ShellCommandType = None) \
        -> tobiko.Selection[P]:
    selection = tobiko.Selection[P](processes)

    if selection and pid is not None:
        # filter files by PID
        selection = selection.with_attributes(pid=pid)

    if selection and command_line is not None:
        if command is None:
            command = _command.shell_command(command_line)[0]

    if selection and command is not None:
        # filter processes by command
        pattern = re.compile(command)
        selection = selection.select(
            lambda process: bool(pattern.match(str(process.command))))

    if selection and is_kernel is not None:
        # filter kernel processes
        selection = selection.with_attributes(is_kernel=bool(is_kernel))

    if selection and command_line is not None:
        pattern = re.compile(str(command_line))
        selection = selection.select(
            lambda process: bool(pattern.match(str(process.command_line))))

    return selection


def list_kernel_processes(**list_params):
    return list_processes(is_kernel=True, **list_params)


def list_all_processes(**list_params):
    return list_processes(is_kernel=None, **list_params)


def list_processes(
        pid: int = None,
        command: str = None,
        is_kernel: typing.Optional[bool] = False,
        ssh_client: ssh.SSHClientType = None,
        command_line: _command.ShellCommandType = None,
        is_cirros: bool = None,
        **execute_params) -> tobiko.Selection[PsProcess]:
    """Returns list of running process

    """
    ps_command = _command.shell_command('ps')
    if pid is None or is_cirros in [True, None]:
        ps_command += '-A'
    else:
        ps_command += f"-p {pid}"

    result = _execute.execute(ps_command,
                              expect_exit_status=None,
                              ssh_client=ssh_client,
                              **execute_params)
    output = result.stdout and result.stdout.strip()
    if not output:
        raise PsError(error=result.stderr)

    # Extract a list of PsProcess instances from table body
    processes = tobiko.Selection[PsProcess]()
    for process_data in parse_table(lines=output.splitlines(),
                                    schema=PS_TABLE_SCHEMA):
        processes.append(PsProcess(ssh_client=ssh_client,
                                   is_cirros=is_cirros,
                                   **process_data))

    return select_processes(processes,
                            pid=pid,
                            command=command,
                            is_kernel=is_kernel,
                            command_line=command_line)


def wait_for_processes(timeout: tobiko.Seconds = None,
                       sleep_interval: tobiko.Seconds = None,
                       ssh_client: ssh.SSHClientType = None,
                       is_cirros: bool = None,
                       **list_params):
    for attempt in tobiko.retry(timeout=timeout,
                                interval=sleep_interval,
                                default_interval=5.):
        processes = list_processes(ssh_client=ssh_client,
                                   is_cirros=is_cirros,
                                   **list_params)
        if not processes:
            break

        hostname = _hostname.get_hostname(ssh_client=ssh_client)
        process_lines = [
            '    {pid} {command}'.format(pid=process.pid,
                                         command=process.command)
            for process in processes]

        if attempt.is_last:
            raise PsWaitTimeout(timeout=timeout, hostname=hostname,
                                processes='\n'.join(process_lines))
        LOG.debug(f"Waiting for process(es) on host {hostname}...\n"
                  '\n'.join(process_lines))


def parse_pid(value):
    return 'pid', int(value)


def parse_command(value):
    return 'command', str(value)


PS_TABLE_SCHEMA = {
    'pid': parse_pid,
    'cmd': parse_command,
    'command': parse_command,
}


def parse_table(lines, schema, header_line=None):
    lines = iter(lines)
    while not header_line:
        header_line = next(lines)

    getters = []
    column_names = header_line.strip().lower().split()
    for position, name in enumerate(column_names):
        getter = schema.get(name)
        if getter:
            getters.append((position, getter))

    for line in lines:
        row = line.strip().split(maxsplit=len(column_names) - 1)
        if row:
            yield dict(getter(row[position])
                       for position, getter in getters)
