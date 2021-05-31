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

import collections
import re
import time
import typing

from oslo_log import log

import tobiko
from tobiko.shell.sh import _command
from tobiko.shell.sh import _exception
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _hostname


LOG = log.getLogger(__name__)


class PsError(tobiko.TobikoException):
    message = "Unable to list processes from host: {error}"


class PsWaitTimeout(PsError):
    message = ("Process(es) still running on host {hostname!r} after "
               "{timeout} seconds:\n{processes!s}")


IS_KERNEL_RE = re.compile('^\\[.*\\]$')


_NOT_FOUND = object()


class PsProcess(collections.namedtuple('PsProcess', ['ssh_client',
                                                     'pid',
                                                     'command'])):
    """Process listed by ps command
    """

    @property
    def is_kernel(self):
        return IS_KERNEL_RE.match(self.command) is not None

    @property
    def command_line(self) -> typing.Optional[_command.ShellCommand]:
        command_line = self.__dict__.get('_command_line', _NOT_FOUND)
        if command_line is _NOT_FOUND:
            command_line = None
            try:
                output = _execute.execute(f'cat /proc/{self.pid}/cmdline',
                                          ssh_client=self.ssh_client).stdout
            except _exception.ShellCommandFailed as ex:
                LOG.error(f"Unable to get process command line: {ex.stderr}")
            else:
                line = _command.ShellCommand(output.strip().split('\0')[:-1])
                if line[0] != self.command:
                    LOG.error(f"Command line of process {self.pid} "
                              "doesn't match its command "
                              f"({self.command}): {line}")
                else:
                    command_line = line
            self.__dict__['command_line'] = command_line
        return command_line


def list_kernel_processes(**list_params):
    return list_processes(is_kernel=True, **list_params)


def list_all_processes(**list_params):
    return list_processes(is_kernel=None, **list_params)


def list_processes(pid=None,
                   command: typing.Optional[str] = None,
                   is_kernel=False,
                   ssh_client=None,
                   command_line: typing.Optional[str] = None,
                   **execute_params) -> tobiko.Selection[PsProcess]:
    """Returns the number of seconds passed since last host reboot

    It reads and parses remote special file /proc/uptime and returns a floating
    point value that represents the number of seconds passed since last host
    reboot
    """
    result = _execute.execute('ps -A', expect_exit_status=None,
                              ssh_client=ssh_client, **execute_params)
    output = result.stdout and result.stdout.strip()
    if result.exit_status or not output:
        raise PsError(error=result.stderr)

    # Extract a list of PsProcess instances from table body
    processes = tobiko.Selection[PsProcess]()
    for process_data in parse_table(lines=output.splitlines(),
                                    schema=PS_TABLE_SCHEMA):
        processes.append(PsProcess(ssh_client=ssh_client, **process_data))

    if processes and pid:
        # filter processes by PID
        pid = int(pid)
        assert pid > 0
        processes = processes.with_attributes(pid=pid)

    if processes and command is not None:
        # filter processes by command
        pattern = re.compile(command)
        processes = tobiko.Selection[PsProcess](
            process
            for process in processes
            if pattern.match(process.command))

    if processes and is_kernel is not None:
        # filter kernel processes
        processes = processes.with_attributes(is_kernel=bool(is_kernel))

    if processes and command_line is not None:
        pattern = re.compile(command_line)
        processes = tobiko.Selection[PsProcess](
            process
            for process in processes
            if (process.command_line is not None and
                pattern.match(f"{process.command_line}")))

    return processes


def wait_for_processes(timeout=float('inf'), sleep_interval=5.,
                       ssh_client=None, **list_params):
    start_time = time.time()
    time_left = timeout
    while True:
        processes = list_processes(timeout=time_left,
                                   ssh_client=ssh_client,
                                   **list_params)
        if not processes:
            break

        time_left = timeout - (time.time() - start_time)
        if time_left < sleep_interval:
            hostname = _hostname.get_hostname(ssh_client=ssh_client)
            process_lines = [
                '    {pid} {command}'.format(pid=process.pid,
                                             command=process.command)
                for process in processes]
            raise PsWaitTimeout(timeout=timeout, hostname=hostname,
                                processes='\n'.join(process_lines))

        time.sleep(sleep_interval)


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
        row = line.strip().split()
        if row:
            yield dict(getter(row[position])
                       for position, getter in getters)
