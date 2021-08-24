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

import typing

import tobiko
from tobiko.shell import sh
from tobiko.shell import ssh


class CurlProcessFixture(tobiko.SharedFixture):

    command: sh.ShellCommand
    process: sh.ShellProcessFixture

    def __init__(self,
                 url: str,
                 head_only: bool = None,
                 location: bool = None,
                 max_redirs: int = None,
                 output_file: str = None,
                 ssh_client=ssh.SSHClientType,
                 **process_params):
        super().__init__()
        tobiko.check_valid_type(head_only, bool, type(None))
        tobiko.check_valid_type(location, bool, type(None))
        tobiko.check_valid_type(max_redirs, int, type(None))
        tobiko.check_valid_type(url, str)
        self.head_only = head_only
        self.location = location
        self.max_redirs = max_redirs
        self.output_file = output_file
        self.process_params = process_params
        self.ssh_client = ssh_client
        self.url = url

    def setup_fixture(self):
        command = self.get_command()
        self.process = sh.process(command,
                                  ssh_client=self.ssh_client,
                                  **self.process_params).execute()

    def start_process(self) -> sh.ShellProcessFixture:
        tobiko.setup_fixture(self)
        return self.process

    def get_command(self) -> sh.ShellCommand:
        try:
            return self.command
        except AttributeError:
            pass
        command = sh.shell_command('curl')
        if self.head_only:
            command += '-I'
        if self.location:
            command += '--location'
        if self.max_redirs is not None:
            command += f"--max-redirs '{self.max_redirs}'"
        command += self.url
        self.command = command
        self.addCleanup(self.del_command)
        return command

    def del_command(self):
        try:
            del self.command
        except AttributeError:
            pass


def get_curl_process(url: str,
                     head_only=False,
                     ssh_client=ssh.SSHClientType,
                     **process_params) \
        -> CurlProcessFixture:
    return CurlProcessFixture(url=url,
                              head_only=head_only,
                              ssh_client=ssh_client,
                              **process_params)


def get_url_header(url: str,
                   location: bool = None,
                   max_redirs: int = None,
                   ssh_client=ssh.SSHClientType,
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
                     location: typing.Optional[bool] = True,
                     max_redirs: int = None,
                     ssh_client=ssh.SSHClientType,
                     retry_timeout: tobiko.Seconds = None,
                     retry_interval: tobiko.Seconds = None,
                     retry_count: int = None,
                     **process_params) \
        -> tobiko.Selection[typing.Dict[str, str]]:
    for attempt in tobiko.retry(count=retry_count,
                                timeout=retry_timeout,
                                interval=retry_interval,
                                default_count=3,
                                default_interval=5.,
                                default_timeout=60.):
        process = get_curl_process(url=url,
                                   location=location,
                                   head_only=True,
                                   max_redirs=max_redirs,
                                   ssh_client=ssh_client,
                                   **process_params).start_process()
        expect_exit_status: typing.Optional[int] = None
        if attempt.is_last:
            expect_exit_status = 0

        result = sh.execute_process(
            process, expect_exit_status=expect_exit_status)
        if result.exit_status == 0:
            break
    else:
        raise RuntimeError("Retry loop broken")

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
