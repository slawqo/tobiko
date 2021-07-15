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
import os
import shlex
import typing

from oslo_log import log

import tobiko
from tobiko.shell import grep
from tobiko.shell import find
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


class LogFileDigger(tobiko.SharedFixture):

    found: typing.MutableMapping[str, None]

    def __init__(self, filename: str,
                 pattern: typing.Optional[str] = None,
                 **execute_params):
        super(LogFileDigger, self).__init__()
        self.filename = filename
        self.pattern = pattern
        self.execute_params = execute_params
        self.found = collections.OrderedDict()

    def setup_fixture(self):
        if self.pattern is not None:
            self.find_lines()

    def cleanup_fixture(self):
        self.found.clear()

    @property
    def found_lines(self) -> typing.List[str]:
        return list(self.found)

    def find_lines(self,
                   pattern: str = None,
                   new_lines=False) \
            -> typing.List[str]:
        if pattern is None:
            pattern = self.pattern
            if pattern is None:
                raise ValueError(f"Invalid pattern: {pattern}")
        elif self.pattern is not None:
            raise NotImplementedError(
                "Combining patterns is not supported")
        try:
            lines = self.grep_lines(pattern,
                                    new_lines=new_lines)
        except grep.NoMatchingLinesFound:
            lines = []
        else:
            if lines:
                lines = [line
                         for line in lines
                         if line not in self.found]
                self.found.update((line, None)
                                  for line in lines)

        if new_lines:
            if lines:
                lines_text = '\n\t'.join(lines)
                LOG.debug('Found new lines:\n'
                          f"\t{lines_text}")
            return lines
        else:
            return list(self.found)

    def find_new_lines(self,
                       pattern: str = None) \
            -> typing.List[str]:
        return self.find_lines(pattern=pattern,
                               new_lines=True)

    def grep_lines(self,
                   pattern: str,
                   new_lines: bool = False) \
            -> typing.List[str]:
        # pylint: disable=unused-argument
        log_files = self.list_log_files()
        return grep.grep_files(pattern=pattern,
                               files=log_files,
                               **self.execute_params)

    def list_log_files(self):
        file_path, file_name = os.path.split(self.filename)
        return find.find_files(path=file_path,
                               name=file_name,
                               **self.execute_params)


class JournalLogDigger(LogFileDigger):

    def grep_lines(self,
                   pattern: str,
                   new_lines: bool = False) \
            -> typing.List[str]:
        try:
            result = sh.execute(["journalctl", '--no-pager',
                                 "--unit", shlex.quote(self.filename),
                                 # "--since", "30 minutes ago",
                                 '--output', 'short-iso',
                                 '--grep', shlex.quote(pattern)],
                                **self.execute_params)
        except sh.ShellCommandFailed as ex:
            if ex.stdout.endswith('-- No entries --\n'):
                ssh_client = self.execute_params.get('ssh_client')
                raise grep.NoMatchingLinesFound(
                    pattern=pattern,
                    files=[self.filename],
                    login=ssh_client and ssh_client.login or None)
            else:
                LOG.exception(f"Error executing journalctl: {ex.stderr}")
                return []
        else:
            lines = [line
                     for line in result.stdout.splitlines()
                     if not line.startswith('-- ')]
            return lines


class MultihostLogFileDigger(tobiko.SharedFixture):

    diggers: typing.Optional[typing.Dict[str, LogFileDigger]] = None

    def __init__(
            self,
            filename: str,
            ssh_clients: typing.Iterable[ssh.SSHClientType] = None,
            file_digger_class: typing.Type[LogFileDigger] = LogFileDigger,
            pattern: str = None,
            **execute_params):
        super(MultihostLogFileDigger, self).__init__()
        self.file_digger_class = file_digger_class
        self.filename = filename
        self.execute_params = execute_params
        self.pattern = pattern
        self.ssh_clients: typing.List[ssh.SSHClientType] = []
        if ssh_clients is not None:
            self.ssh_clients.extend(ssh_clients)

    def setup_fixture(self):
        for ssh_client in self.ssh_clients:
            self.add_host(ssh_client=ssh_client)
        if self.diggers is not None:
            for digger in self.diggers.values():
                self.useFixture(digger)

    def cleanup_fixture(self):
        self.diggers = None

    def add_host(self,
                 ssh_client: ssh.SSHClientType,
                 hostname: str = None):
        if self.diggers is None:
            self.diggers = collections.OrderedDict()
        if hostname is None:
            hostname = sh.get_hostname(ssh_client=ssh_client)
        digger = self.diggers.get(hostname)
        if digger is None:
            self.diggers[hostname] = digger = self.file_digger_class(
                filename=self.filename,
                ssh_client=ssh_client,
                pattern=self.pattern,
                **self.execute_params)
        return digger

    @property
    def found_lines(self) \
            -> typing.List[typing.Tuple[str, str]]:
        # ensure diggers are ready before looking for lines
        tobiko.setup_fixture(self)
        lines: typing.List[typing.Tuple[str, str]] = []
        if self.diggers is not None:
            for hostname, digger in self.diggers.items():
                for line in digger.found_lines:
                    lines.append((hostname, line))
        return lines

    def find_lines(self,
                   pattern: str = None,
                   new_lines: bool = False) \
            -> typing.List[typing.Tuple[str, str]]:
        # ensure diggers are ready before looking for lines
        tobiko.setup_fixture(self)
        lines: typing.List[typing.Tuple[str, str]] = []
        if self.diggers is not None:
            for hostname, digger in self.diggers.items():
                for line in digger.find_lines(pattern=pattern,
                                              new_lines=new_lines):
                    lines.append((hostname, line))
        return lines

    def find_new_lines(self,
                       pattern: str = None,
                       retry_count: int = None,
                       retry_timeout: tobiko.Seconds = 60.,
                       retry_interval: tobiko.Seconds = None) \
            -> typing.List[typing.Tuple[str, str]]:
        for _ in tobiko.retry(count=retry_count,
                              timeout=retry_timeout,
                              interval=retry_interval,
                              default_interval=1.,
                              default_timeout=60.):
            new_lines = self.find_lines(pattern=pattern,
                                        new_lines=True)
            if new_lines:
                break
        else:
            raise RuntimeError("Internal bug: retry loop break itself.")

        return new_lines
