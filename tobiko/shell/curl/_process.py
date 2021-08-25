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

import os
import typing

from oslo_log import log

import tobiko
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


class CurlProcessFixture(tobiko.SharedFixture):

    _command: sh.ShellCommand
    _process: sh.ShellProcessFixture
    _result: sh.ShellExecuteResult

    def __init__(self,
                 url: str,
                 continue_at: int = None,
                 create_dirs: bool = None,
                 head: bool = None,
                 location: bool = None,
                 max_redirs: int = None,
                 output_filename: str = None,
                 ssh_client: ssh.SSHClientType = None,
                 sudo: bool = None):
        super().__init__()
        tobiko.check_valid_type(continue_at, int, type(None))
        tobiko.check_valid_type(create_dirs, bool, type(None))
        tobiko.check_valid_type(head, bool, type(None))
        tobiko.check_valid_type(location, bool, type(None))
        tobiko.check_valid_type(max_redirs, int, type(None))
        tobiko.check_valid_type(output_filename, str, type(None))
        tobiko.check_valid_type(ssh_client, ssh.SSHClientFixture, bool,
                                type(None))
        tobiko.check_valid_type(sudo, bool, type(None))
        tobiko.check_valid_type(url, str)
        self.continue_at = continue_at
        self.create_dirs = create_dirs
        self.head = head
        self.location = location
        self.max_redirs = max_redirs
        self.output_filename = output_filename
        self.ssh_client = ssh_client
        self.sudo = sudo
        self.url = url

    @property
    def command(self) -> sh.ShellCommand:
        try:
            return self._command
        except AttributeError:
            pass
        command = sh.shell_command('curl') + self.get_options() + self.url
        self._command = command
        self.addCleanup(self._del_command)
        return command

    def _del_command(self):
        try:
            del self._command
        except AttributeError:
            pass

    @property
    def process(self) -> sh.ShellProcessFixture:
        try:
            return self._process
        except AttributeError:
            raise RuntimeError("Curl process not stated") from None

    def setup_fixture(self):
        self._process = sh.process(self.command,
                                   ssh_client=self.ssh_client,
                                   sudo=self.sudo)
        self.useFixture(self.process)

    def start(self) -> 'CurlProcessFixture':
        return tobiko.setup_fixture(self)

    def stop(self) -> 'CurlProcessFixture':
        try:
            process = self._process
        except RuntimeError:
            pass  # process not started
        else:
            process.kill(sudo=self.sudo)
        return tobiko.cleanup_fixture(self)

    def execute(self,
                retry_count: int = None,
                retry_timeout: tobiko.Seconds = None,
                retry_interval: tobiko.Seconds = None) -> \
            sh.ShellExecuteResult:
        for attempt in tobiko.retry(count=retry_count,
                                    timeout=retry_timeout,
                                    interval=retry_interval,
                                    default_count=1):
            self.start()
            result = self.wait(check=attempt.is_last)
            if result.exit_status == 0:
                break
            self.stop()
        else:
            raise RuntimeError("Retry loop broken")
        return result

    def wait(self,
             check: bool = False,
             expect_exit_status: int = None) \
            -> sh.ShellExecuteResult:
        if expect_exit_status is None and check:
            expect_exit_status = 0
        self._result = result = sh.execute_process(
            self.process, expect_exit_status=expect_exit_status)
        return result

    @property
    def result(self) -> sh.ShellExecuteResult:
        try:
            return self._result
        except AttributeError:
            raise RuntimeError("Process not terminated") from None

    def get_options(self) -> sh.ShellCommand:
        options = sh.ShellCommand()
        if self.continue_at:
            if self.continue_at < 0:
                options += "-C -"
            else:
                options += f"-C '{self.continue_at}'"
        if self.create_dirs:
            options += '--create-dirs'
        if self.head:
            options += '-I'
        if self.location:
            options += '-L'
        if self.max_redirs is not None:
            options += f"--max-redirs '{self.max_redirs}'"
        if self.output_filename:
            options += f"-o '{self.output_filename}'"
        return options

    def open_output_file(self):
        tobiko.check_valid_type(self.output_filename, str)
        assert self.output_filename


def curl_process(url: str,
                 continue_at: int = None,
                 create_dirs: bool = None,
                 head: bool = None,
                 location: bool = None,
                 max_redirs: int = None,
                 output_filename: str = None,
                 ssh_client: ssh.SSHClientType = None,
                 sudo: bool = None) \
        -> CurlProcessFixture:
    return CurlProcessFixture(url=url,
                              continue_at=continue_at,
                              create_dirs=create_dirs,
                              head=head,
                              location=location,
                              max_redirs=max_redirs,
                              output_filename=output_filename,
                              ssh_client=ssh_client,
                              sudo=sudo)


def get_url_header(url: str,
                   location: bool = None,
                   max_redirs: int = None,
                   ssh_client: ssh.SSHClientType = None,
                   retry_timeout: tobiko.Seconds = None,
                   retry_interval: tobiko.Seconds = None,
                   retry_count: int = None,
                   **process_params) -> typing.Dict[str, str]:
    headers = list_url_headers(url=url,
                               location=location,
                               max_redirs=max_redirs,
                               ssh_client=ssh_client,
                               retry_timeout=retry_timeout,
                               retry_interval=retry_interval,
                               retry_count=retry_count,
                               **process_params)
    return headers[-1]


def list_url_headers(url: str,
                     location: bool = None,
                     max_redirs: int = None,
                     ssh_client: ssh.SSHClientType = None,
                     retry_timeout: tobiko.Seconds = None,
                     retry_interval: tobiko.Seconds = None,
                     retry_count: int = None,
                     sudo: bool = None) \
        -> tobiko.Selection[typing.Dict[str, str]]:
    if location is None:
        location = True
    process = curl_process(url=url,
                           location=location,
                           head=True,
                           max_redirs=max_redirs,
                           ssh_client=ssh_client,
                           sudo=sudo)
    result = process.execute(retry_count=retry_count,
                             retry_timeout=retry_timeout,
                             retry_interval=retry_interval)
    headers = tobiko.Selection[typing.Dict[str, str]]()
    header: typing.Dict[str, str] = {}
    line: str
    header_lines = result.stdout.splitlines()
    for line in header_lines:
        line = line.strip()
        if not line:
            if header:
                headers.append(header)
                header = {}
        elif ':' in line:
            key, value = line.split(':', 1)
            header[key.lower().strip()] = value.strip()
    if header:
        headers.append(header)
    return headers


def default_download_dirname() -> str:
    return '~/.tobiko/download'


def download_file(url: str,
                  output_filename: str = None,
                  download_dirname: str = None,
                  continue_at: int = None,
                  create_dirs: bool = None,
                  location: bool = None,
                  max_redirs: int = None,
                  wait=True,
                  retry_count: int = None,
                  retry_timeout: tobiko.Seconds = None,
                  retry_interval: tobiko.Seconds = None,
                  ssh_client: ssh.SSHClientType = None,
                  sudo: bool = None):
    if location is None:
        location = True
    if output_filename is None:
        if download_dirname is None:
            download_dirname = default_download_dirname()
            create_dirs = True
        output_filename = os.path.join(download_dirname,
                                       os.path.basename(url))
    process = curl_process(url=url,
                           output_filename=output_filename,
                           continue_at=continue_at,
                           create_dirs=create_dirs,
                           location=location,
                           max_redirs=max_redirs,
                           ssh_client=ssh_client,
                           sudo=sudo)
    LOG.debug(f"Downloading file ('{url}' -> '{output_filename}')...")
    if wait:
        process.execute(retry_count=retry_count,
                        retry_timeout=retry_timeout,
                        retry_interval=retry_interval)
        LOG.debug(f"File download complete ('{url}' -> '{output_filename}').")
    else:
        process.start()
    return process
