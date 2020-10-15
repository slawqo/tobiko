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

import os

from tobiko.shell import files
from tobiko.shell import sh
from tobiko.openstack import topology


class LogFile(object):

    def __init__(self, hostname, filename):
        self.filename = filename
        self.host = topology.get_openstack_node(hostname=hostname)
        self._list_logfiles()
        self.cmd = ''
        self.found = []

    def find(self, regex):
        self._list_logfiles()
        self.cmd = f"zgrep -Eh {regex}"
        self.found = sh.execute(f'{self.cmd} {" ".join(self.logfiles)}',
                                ssh_client=self.host.ssh_client,
                                expect_exit_status=None,
                                sudo=True).stdout.split('\n')
        try:
            self.found.remove('')
        except ValueError:
            pass
        return self.found

    def find_new(self):
        self._list_logfiles()
        if not self.cmd:
            err_msg = 'find_new() method can be only executed after find()'
            raise files.LogParserError(message=err_msg)
        tmp = sh.execute(f'{self.cmd} {" ".join(self.logfiles)}',
                         ssh_client=self.host.ssh_client,
                         expect_exit_status=None,
                         sudo=True).stdout.split('\n')
        found = []
        for log_string in tmp:
            if log_string not in self.found and log_string != '':
                found.append(log_string)
                self.found.append(log_string)
        return found

    def _list_logfiles(self):
        file_path, file_name = os.path.split(self.filename)
        result = sh.execute(f'find {file_path} -name {file_name}*',
                            ssh_client=self.host.ssh_client,
                            expect_exit_status=None,
                            sudo=True)
        self.logfiles = set(result.stdout.split('\n'))
        if '' in self.logfiles:
            self.logfiles.remove('')
        if self.logfiles == []:
            raise files.LogFileNotFound(filename=str(self.filename),
                                        host=str(self.host.name))


class ClusterLogFile(object):

    def __init__(self, filename):
        self.filename = filename
        self.hostnames = []
        self.logfiles = []

    def add_host(self, hostname):
        if hostname in self.hostnames:
            return
        self.hostnames.append(hostname)
        self.logfiles.append(LogFile(hostname, self.filename))

    def add_group(self, group):
        for host in topology.list_openstack_nodes(group=group):
            self.add_host(host.name)

    def find(self, regex):
        for logfile in self.logfiles:
            logfile.find(regex)
        return self.found

    def find_new(self):
        new_lines = []
        for logfile in self.logfiles:
            new_lines += logfile.find_new()
        return new_lines

    @property
    def found(self):
        found = []
        for logfile in self.logfiles:
            found += logfile.found
        return found
