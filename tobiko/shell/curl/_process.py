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

import collections
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
                 file_name: str = None,
                 head_only: bool = None,
                 headers_file_name: str = None,
                 location: bool = None,
                 max_redirs: int = None,
                 ssh_client: ssh.SSHClientType = None,
                 sudo: bool = None):
        super().__init__()
        tobiko.check_valid_type(continue_at, int, type(None))
        tobiko.check_valid_type(create_dirs, bool, type(None))
        tobiko.check_valid_type(head_only, bool, type(None))
        tobiko.check_valid_type(location, bool, type(None))
        tobiko.check_valid_type(max_redirs, int, type(None))
        tobiko.check_valid_type(file_name, str, type(None))
        tobiko.check_valid_type(headers_file_name, str, type(None))
        tobiko.check_valid_type(ssh_client, ssh.SSHClientFixture, bool,
                                type(None))
        tobiko.check_valid_type(sudo, bool, type(None))
        tobiko.check_valid_type(url, str)
        self.continue_at = continue_at
        self.create_dirs = create_dirs
        self.head_only = head_only
        self.headers_file_name = headers_file_name
        self.location = location
        self.max_redirs = max_redirs
        self.file_name = file_name
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
        if self.create_dirs and self.headers_file_name is not None:
            headers_dir = os.path.dirname(self.headers_file_name)
            sh.execute(f'mkdir -p "{headers_dir}"',
                       ssh_client=self.ssh_client,
                       sudo=self.sudo)
        process = sh.process(self.command,
                             ssh_client=self.ssh_client,
                             sudo=self.sudo)
        self._process = self.useFixture(process)

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
        if self.executed:
            return self._result
        else:
            raise RuntimeError("Process not terminated") from None

    @property
    def executed(self) -> bool:
        return hasattr(self, '_result')

    def get_options(self) -> sh.ShellCommand:
        options = sh.ShellCommand()
        if self.continue_at:
            if self.continue_at < 0:
                options += "-C -"
            else:
                options += f"-C '{self.continue_at}'"
        if self.create_dirs:
            options += '--create-dirs'
        if self.head_only:
            options += '-I'
        if self.headers_file_name:
            options += f'-D "{self.headers_file_name}"'
        if self.location:
            options += '-L'
        if self.max_redirs is not None:
            options += f"--max-redirs '{self.max_redirs}'"
        if self.file_name:
            options += f"-o '{self.file_name}'"
        return options

    def open_output_file(self):
        tobiko.check_valid_type(self.file_name, str)
        assert self.file_name


def curl_process(url: str,
                 continue_at: int = None,
                 create_dirs: bool = None,
                 head_only: bool = None,
                 headers_file_name: str = None,
                 location: bool = None,
                 max_redirs: int = None,
                 file_name: str = None,
                 ssh_client: ssh.SSHClientType = None,
                 sudo: bool = None) \
        -> CurlProcessFixture:
    return CurlProcessFixture(url=url,
                              continue_at=continue_at,
                              create_dirs=create_dirs,
                              head_only=head_only,
                              headers_file_name=headers_file_name,
                              location=location,
                              max_redirs=max_redirs,
                              file_name=file_name,
                              ssh_client=ssh_client,
                              sudo=sudo)


class CurlHeader(collections.UserDict):

    def __init__(self,
                 head_line: typing.Optional[str],
                 *args,
                 **kwargs):
        self.head_line = head_line
        super(CurlHeader, self).__init__(*args, **kwargs)

    @property
    def content_length(self) -> typing.Optional[int]:
        length = self.get('content-length')
        if length is None:
            return None
        else:
            return int(length)

    def __repr__(self):
        entries = super().__repr__()
        return f"CurlHeader({self.head_line!r}, {entries})"


def get_url_header(url: str,
                   location: typing.Optional[bool] = True,
                   max_redirs: int = None,
                   ssh_client: ssh.SSHClientType = None,
                   retry_timeout: tobiko.Seconds = None,
                   retry_interval: tobiko.Seconds = None,
                   retry_count: int = None,
                   **process_params) -> CurlHeader:
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
                     location: typing.Optional[bool] = True,
                     max_redirs: int = None,
                     ssh_client: ssh.SSHClientType = None,
                     retry_timeout: tobiko.Seconds = None,
                     retry_interval: tobiko.Seconds = None,
                     retry_count: int = None,
                     sudo: bool = None) \
        -> tobiko.Selection[CurlHeader]:
    process = curl_process(url=url,
                           location=location,
                           head_only=True,
                           max_redirs=max_redirs,
                           ssh_client=ssh_client,
                           sudo=sudo)
    result = process.execute(retry_count=retry_count,
                             retry_timeout=retry_timeout,
                             retry_interval=retry_interval)
    return parse_headers(result.stdout)


def read_headers_file(headers_file_name: str,
                      ssh_client: ssh.SSHClientType = None,
                      sudo: bool = None) \
        -> tobiko.Selection[CurlHeader]:
    result = sh.execute(f'cat "{headers_file_name}"',
                        ssh_client=ssh_client,
                        sudo=sudo)
    return parse_headers(result.stdout)


def parse_headers(headers_text: str) \
        -> tobiko.Selection[CurlHeader]:
    headers = tobiko.Selection[CurlHeader]()
    entries: typing.Dict[str, str] = {}
    line_number = 0
    head_line: typing.Optional[str] = None
    for line in headers_text.splitlines():
        line = line.strip()
        line_number += 1
        if not line:
            if entries:
                headers.append(CurlHeader(head_line, entries))
                head_line = None
                entries = {}
        elif ':' in line:
            key, value = line.split(':', 1)
            entries[key.lower().strip()] = value.strip()
        elif len(entries) == 0:
            head_line = line
        else:
            raise ValueError(f'Invalid line {line_number} in header: {line}\n"'
                             f'"{headers_text}')
    if entries:
        headers.append(CurlHeader(head_line, entries))
    return headers


def default_download_dir() -> str:
    return '~/.tobiko/download'


def download_file(url: str,
                  file_name: str = None,
                  cached: bool = False,
                  check: bool = True,
                  download_dir: str = None,
                  continue_at: int = None,
                  create_dirs: bool = None,
                  headers_file_name: str = None,
                  location: typing.Optional[bool] = True,
                  max_redirs: int = None,
                  wait: bool = True,
                  retry_count: int = None,
                  retry_timeout: tobiko.Seconds = None,
                  retry_interval: tobiko.Seconds = None,
                  ssh_client: ssh.SSHClientType = None,
                  sudo: bool = None) \
        -> CurlProcessFixture:
    if file_name is None:
        if download_dir is None:
            download_dir = default_download_dir()
            create_dirs = True
        file_name = os.path.join(download_dir,
                                 os.path.basename(url))
    if headers_file_name is None:
        headers_file_name = file_name + '.headers'
        create_dirs = True

    process = curl_process(url=url,
                           file_name=file_name,
                           headers_file_name=headers_file_name,
                           continue_at=continue_at,
                           create_dirs=create_dirs,
                           location=location,
                           max_redirs=max_redirs,
                           ssh_client=ssh_client,
                           sudo=sudo)
    if cached:
        try:
            assert_downloaded_file(file_name=file_name,
                                   headers_file_name=headers_file_name,
                                   ssh_client=ssh_client,
                                   sudo=sudo)
        except tobiko.FailureException:  # type: ignore
            pass
        else:
            LOG.debug(f"File '{url}' already downloaded.")
            return process

    LOG.debug(f"Downloading file ('{url}' -> '{file_name}')...")
    if not wait:
        process.start()
        return process

    process.execute(retry_count=retry_count,
                    retry_timeout=retry_timeout,
                    retry_interval=retry_interval)
    LOG.debug(f"File download complete ('{url}' -> '{file_name}').")
    if check:
        assert_downloaded_file(file_name=file_name,
                               headers_file_name=headers_file_name,
                               ssh_client=ssh_client,
                               sudo=sudo)
    return process


def assert_downloaded_file(file_name: str,
                           headers_file_name: str,
                           ssh_client: ssh.SSHClientType = None,
                           sudo: bool = None):
    try:
        header = read_headers_file(headers_file_name=headers_file_name,
                                   ssh_client=ssh_client,
                                   sudo=sudo)[-1]
    except sh.ShellCommandFailed as ex:
        tobiko.fail(f"Error reading headers file '{headers_file_name}': {ex}")
    else:
        file_size = header.content_length
        if file_size is not None:
            sh.assert_file_size(file_size=header.content_length,
                                file_name=file_name,
                                ssh_client=ssh_client,
                                sudo=sudo)
