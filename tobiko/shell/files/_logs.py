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

from tobiko.shell import grep
from tobiko.shell import find
from tobiko.shell import sh


class LogFileDigger(object):

    def __init__(self, filename, **execute_params):
        self.filename = filename
        self.execute_params = execute_params
        self.logfiles = set()
        self.found = set()

    def find_lines(self, pattern, new_lines=False):
        log_files = self.list_log_files()
        try:
            lines = frozenset(
                grep.grep_files(pattern=pattern, files=log_files,
                                **self.execute_params))
        except grep.NoMatchingLinesFound:
            if new_lines:
                return frozenset()
        else:
            lines -= self.found
            self.found.update(lines)
            if new_lines:
                return lines
        return frozenset(self.found)

    def find_new_lines(self, pattern):
        return self.find_lines(pattern=pattern, new_lines=True)

    def list_log_files(self):
        file_path, file_name = os.path.split(self.filename)
        return find.find_files(path=file_path,
                               name=file_name,
                               **self.execute_params)


class JournalLogDigger(LogFileDigger):

    def find_lines(self, pattern, new_lines=False):
        dump_log_cmd = [
            "journalctl", "--unit", self.filename,
            "--since", "5 minutes ago"]
        try:
            lines = frozenset(
                grep.grep_lines(pattern=pattern,
                                command=dump_log_cmd,
                                **self.execute_params))
        except grep.NoMatchingLinesFound:
            if new_lines:
                return frozenset()
        else:
            lines -= self.found
            self.found.update(lines)
            if new_lines:
                return lines
        return frozenset(self.found)


class MultihostLogFileDigger(object):

    def __init__(self, filename, ssh_clients=None,
                 file_digger_class=LogFileDigger,
                 **execute_params):
        self.diggers = collections.OrderedDict()
        self.file_digger_class = file_digger_class
        self.filename = filename
        self.execute_params = execute_params
        if ssh_clients:
            for ssh_client in ssh_clients:
                self.add_host(ssh_client=ssh_client)

    def add_host(self, hostname=None, ssh_client=None):
        hostname = hostname or sh.get_hostname(ssh_client=ssh_client)
        if hostname not in self.diggers:
            self.diggers[hostname] = self.file_digger_class(
                filename=self.filename,
                ssh_client=ssh_client,
                **self.execute_params)

    def find_lines(self, pattern, new_lines=False):
        lines = []
        for hostname, digger in self.diggers.items():
            for line in digger.find_lines(pattern, new_lines=new_lines):
                lines.append((hostname, line))
        return lines

    def find_new_lines(self, pattern):
        return self.find_lines(pattern=pattern, new_lines=True)
