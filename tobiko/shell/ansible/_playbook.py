# Copyright (c) 2022 Red Hat, Inc.
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
import typing

import tobiko
from tobiko.shell import sh
from tobiko.shell import ssh


class AnsiblePlaybook(tobiko.SharedFixture):

    def __init__(self,
                 command: sh.ShellCommandType = 'ansible-playbook',
                 inventory_filename: str = None,
                 playbook: str = 'main',
                 playbook_dirname: str = None,
                 ssh_client: ssh.SSHClientType = None,
                 work_dir: str = None):
        super(AnsiblePlaybook, self).__init__()
        self._command = sh.shell_command(command)
        self._inventory_filename = inventory_filename
        self._playbook = playbook
        self._playbook_dirname = playbook_dirname
        self._ssh_client = ssh_client
        self._work_dir = work_dir
        self._work_files: typing.Dict[str, str] = {}

    def setup_fixture(self):
        pass

    @property
    def ssh_client(self) -> ssh.SSHClientType:
        return self._ssh_client

    _sh_connection: typing.Optional[sh.ShellConnection] = None

    @property
    def sh_connection(self) -> sh.ShellConnection:
        if self._sh_connection is None:
            self._sh_connection = sh.shell_connection(
                ssh_client=self.ssh_client)
        return self._sh_connection

    @property
    def work_dir(self) -> str:
        if self._work_dir is None:
            self._work_dir = self.sh_connection.make_temp_dir(auto_clean=False)
            self._work_files = {}
        return self._work_dir

    @property
    def playbook_dirname(self) -> str:
        return tobiko.check_valid_type(self._playbook_dirname, str)

    def _ensure_inventory_filename(self, inventory_filename: str = None) \
            -> typing.Optional[str]:
        if inventory_filename is None:
            inventory_filename = self._inventory_filename
        if inventory_filename is None:
            return None
        return self._ensure_work_file(inventory_filename, 'inventory')

    def _get_playbook_filename(self,
                               basename: str = None,
                               dirname: str = None) -> str:
        if basename is None:
            basename = self._playbook
        if dirname is None:
            dirname = self.playbook_dirname
        return os.path.join(dirname, basename)

    def _ensure_vars_files(self,
                           vars_files: typing.Iterable[str],
                           sub_dir: str = None,
                           dirname: str = None) -> typing.List[str]:
        work_filenames = []
        for vars_file in vars_files:
            filename = self._get_playbook_filename(basename=vars_file,
                                                   dirname=dirname)
            if sub_dir is None and dirname is not None:
                sub_dir = os.path.relpath(os.path.dirname(filename), dirname)

            work_filename = self._ensure_work_file(filename=filename,
                                                   sub_dir=sub_dir)
            work_filenames.append(work_filename)
        return work_filenames

    def _ensure_work_file(self, filename: str, sub_dir: str = None) -> str:
        filename = os.path.realpath(filename)
        work_filename = self._work_files.get(filename)
        if work_filename is None:
            if sub_dir is not None:
                work_filename = os.path.join(
                    self.work_dir, sub_dir, os.path.basename(filename))
            else:
                work_filename = os.path.join(
                    self.work_dir, os.path.basename(filename))
            if sub_dir is not None:
                self.sh_connection.make_dirs(os.path.dirname(work_filename))
            self.sh_connection.put_file(filename, work_filename)
            self._work_files[filename] = work_filename
        return work_filename

    def cleanup_fixture(self):
        self._sh_connection = None
        self._work_files = None
        if self._work_dir is not None:
            self.sh_connection.remove_files(self._work_dir)
            self._work_dir = None

    def _get_command(self,
                     command: sh.ShellCommandType = None,
                     playbook: str = None,
                     playbook_dirname: str = None,
                     playbook_filename: str = None,
                     inventory_filename: str = None,
                     vars_files: typing.Iterable[str] = None) -> \
            sh.ShellCommand:
        # ensure command
        if command is None:
            command = self._command
        assert isinstance(command, sh.ShellCommand)

        # ensure inventory
        work_inventory_filename = self._ensure_inventory_filename(
            inventory_filename)
        if work_inventory_filename is not None:
            command += ['-i', work_inventory_filename]

        # ensure playbook file
        if playbook_filename is None:
            playbook_filename = self._get_playbook_filename(
                basename=playbook, dirname=playbook_dirname)
            playbook_dirname = os.path.dirname(playbook_filename)
        command += [self._ensure_work_file(playbook_filename)]

        if vars_files is not None:
            self._ensure_vars_files(vars_files=vars_files,
                                    dirname=playbook_dirname)
        return command

    def run_playbook(self,
                     command: sh.ShellCommand = None,
                     playbook: str = None,
                     playbook_dirname: str = None,
                     playbook_filename: str = None,
                     inventory_filename: str = None,
                     vars_files: typing.Iterable[str] = None):
        tobiko.setup_fixture(self)
        command = self._get_command(command=command,
                                    playbook=playbook,
                                    playbook_dirname=playbook_dirname,
                                    playbook_filename=playbook_filename,
                                    inventory_filename=inventory_filename,
                                    vars_files=vars_files)
        return self.sh_connection.execute(command, current_dir=self.work_dir)


def local_ansible_playbook() -> 'AnsiblePlaybook':
    return tobiko.get_fixture(AnsiblePlaybook)


def ansible_playbook(ssh_client: ssh.SSHClientType = None,
                     manager: 'AnsiblePlaybookManager' = None) -> \
        'AnsiblePlaybook':
    return ansible_playbook_manager(manager).get_ansible_playbook(
        ssh_client=ssh_client)


def register_ansible_playbook(playbook: 'AnsiblePlaybook',
                              manager: 'AnsiblePlaybookManager' = None) -> \
        None:
    tobiko.check_valid_type(playbook, AnsiblePlaybook)
    ansible_playbook_manager(manager).register_ansible_playbook(playbook)


def ansible_playbook_manager(manager: 'AnsiblePlaybookManager' = None) -> \
        'AnsiblePlaybookManager':
    if manager is None:
        return tobiko.setup_fixture(AnsiblePlaybookManager)
    else:
        tobiko.check_valid_type(manager, AnsiblePlaybookManager)
        return manager


AnsiblePlaybookKey = typing.Optional[ssh.SSHClientFixture]


class AnsiblePlaybookManager(tobiko.SharedFixture):

    def __init__(self):
        super(AnsiblePlaybookManager, self).__init__()
        self._host_playbooks: typing.Dict['AnsiblePlaybookKey',
                                          'AnsiblePlaybook'] = {}

    def get_ansible_playbook(self,
                             ssh_client: ssh.SSHClientType) -> \
            'AnsiblePlaybook':
        ssh_client = ssh.ssh_client_fixture(ssh_client)
        playbook = self._host_playbooks.get(ssh_client)
        if playbook is None:
            playbook = self._init_ansible_playbook(ssh_client=ssh_client)
            self._host_playbooks[ssh_client] = playbook
        return playbook

    def register_ansible_playbook(self, playbook: 'AnsiblePlaybook'):
        ssh_client = ssh.ssh_client_fixture(playbook.ssh_client)
        self._host_playbooks[ssh_client] = playbook

    @staticmethod
    def _init_ansible_playbook(ssh_client: ssh.SSHClientFixture = None) \
            -> 'AnsiblePlaybook':
        if ssh_client is None:
            return local_ansible_playbook()
        else:
            return tobiko.get_fixture(AnsiblePlaybook(ssh_client=ssh_client))


def run_playbook(command: sh.ShellCommand = None,
                 playbook: str = None,
                 playbook_dirname: str = None,
                 playbook_filename: str = None,
                 inventory_filename: str = None,
                 ssh_client: ssh.SSHClientType = None,
                 manager: AnsiblePlaybookManager = None) \
        -> sh.ShellExecuteResult:
    return ansible_playbook(ssh_client=ssh_client,
                            manager=manager).run_playbook(
                            command=command,
                            playbook=playbook,
                            playbook_dirname=playbook_dirname,
                            playbook_filename=playbook_filename,
                            inventory_filename=inventory_filename)
