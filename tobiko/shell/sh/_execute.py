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

import collections
import subprocess
import sys

from oslo_log import log
import six

from tobiko.shell.sh import _exception


LOG = log.getLogger(__name__)


def execute(command, timeout=None, shell=None, check=True, ssh_client=None):
    """Execute command inside a remote or local shell

    :param command: command argument list

    :param timeout: command execution timeout in seconds

    :param check: when False it doesn't raises ShellCommandError when
    exit status is not zero. True by default

    :param ssh_client: SSH client instance used for remote shell execution

    :returns: STDOUT text when command execution terminates with zero exit
    status.

    :raises ShellTimeoutExpired: when timeout expires before command execution
    terminates. In such case it kills the process, then it eventually would
    try to read STDOUT and STDERR buffers (not fully implemented) before
    raising the exception.

    :raises ShellCommandError: when command execution terminates with non-zero
    exit status.
    """
    if timeout:
        timeout = float(timeout)

    if ssh_client:
        result = execute_remote_command(command=command, timeout=timeout,
                                        shell=shell, ssh_client=ssh_client)
    else:
        result = execute_local_command(command=command, timeout=timeout,
                                       shell=shell)

    if result.exit_status == 0:
        LOG.debug("Command %r succeeded:\n"
                  "stderr:\n%s\n"
                  "stdout:\n%s\n",
                  command, result.stderr, result.stdout)
    elif result.exit_status is None:
        LOG.debug("Command %r timeout expired (timeout=%s):\n"
                  "stderr:\n%s\n"
                  "stdout:\n%s\n",
                  command, timeout, result.stderr, result.stdout)
    else:
        LOG.debug("Command %r failed (exit_status=%s):\n"
                  "stderr:\n%s\n"
                  "stdout:\n%s\n",
                  command, result.exit_status, result.stderr, result.stdout)
    if check:
        result.check()

    return result


def execute_remote_command(command, ssh_client, timeout=None, shell=None):
    """Execute command on a remote host using SSH client"""
    raise NotImplementedError


def execute_local_command(command, timeout=None, shell=None):
    """Execute command on local host using local shell"""

    LOG.debug("Executing command %r on local host (timeout=%r)...",
              command, timeout)

    if not shell:
        from tobiko import config
        CONF = config.CONF
        shell = CONF.tobiko.shell.command

    if isinstance(command, six.string_types):
        command = command.split()
    else:
        command = [str(a) for a in command]

    if shell:
        command = shell.split() + [str(subprocess.list2cmdline(command))]
    process = subprocess.Popen(command,
                               universal_newlines=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    if timeout and sys.version_info < (3, 3):
        LOG.warning("Popen.communicate method doens't support for timeout "
                    "on Python %r", sys.version)
        timeout = None

    # Wait for process execution while reading STDERR and STDOUT streams
    if timeout:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # At this state I expect the process to be still running
            # therefore it has to be kill later after calling poll()
            LOG.exception("Command %r timeout expired.", command)
            stdout = stderr = None
    else:
        stdout, stderr = process.communicate()

    # Check process termination status
    exit_status = process.poll()
    if exit_status is None:
        # The process is still running after calling communicate():
        # let kill it
        process.kill()

    return ShellExecuteResult(command=command, timeout=timeout,
                              stdout=stdout, stderr=stderr,
                              exit_status=exit_status)


class ShellExecuteResult(collections.namedtuple(
        'ShellExecuteResult', ['command', 'timeout', 'exit_status', 'stdout',
                               'stderr'])):

    def check(self):
        if self.exit_status is None:
            raise _exception.ShellTimeoutExpired(command=self.command,
                                                 timeout=self.timeout,
                                                 stderr=self.stderr,
                                                 stdout=self.stdout)

        elif self.exit_status != 0:
            raise _exception.ShellCommandFailed(command=self.command,
                                                exit_status=self.exit_status,
                                                stderr=self.stderr,
                                                stdout=self.stdout)
