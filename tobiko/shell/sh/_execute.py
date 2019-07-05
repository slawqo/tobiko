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


from oslo_log import log
import six

from tobiko.shell.sh import _process


LOG = log.getLogger(__name__)


DATA_TYPES = six.string_types + (six.binary_type, six.text_type)


class ShellExecuteResult(object):

    def __init__(self, command=None, exit_status=None, stdin=None, stdout=None,
                 stderr=None):
        self.command = str(command)
        self.exit_status = int(exit_status)
        self.stdin = stdin and str(stdin) or None
        self.stdout = stdout and str(stdout) or None
        self.stderr = stderr and str(stderr) or None


def execute(command, environment=None, timeout=None, shell=None,
            stdin=None, stdout=None, stderr=None, ssh_client=None,
            expect_exit_status=0, **kwargs):
    """Execute command inside a remote or local shell

    :param command: command argument list

    :param timeout: command execution timeout in seconds

    :param check: when False it doesn't raises ShellCommandError when
    exit status is not zero. True by default

    :param ssh_client: SSH client instance used for remote shell execution

    :raises ShellTimeoutExpired: when timeout expires before command execution
    terminates. In such case it kills the process, then it eventually would
    try to read STDOUT and STDERR buffers (not fully implemented) before
    raising the exception.

    :raises ShellCommandError: when command execution terminates with non-zero
    exit status.
    """
    process = _process.process(command=command,
                               environment=environment,
                               timeout=timeout,
                               shell=shell,
                               stdin=stdin,
                               stdout=stdout,
                               stderr=stderr,
                               ssh_client=ssh_client,
                               **kwargs)
    return execute_process(process=process,
                           stdin=stdin,
                           expect_exit_status=expect_exit_status)


def execute_process(process, stdin, expect_exit_status):
    with process:
        if stdin and isinstance(stdin, DATA_TYPES):
            process.send(data=stdin)
    if expect_exit_status is not None:
        process.check_exit_status(expect_exit_status)

    return ShellExecuteResult(command=str(process.command),
                              exit_status=int(process.exit_status),
                              stdin=_process.str_from_stream(process.stdin),
                              stdout=_process.str_from_stream(process.stdout),
                              stderr=_process.str_from_stream(process.stderr))
