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

import fcntl
import os
import subprocess

from oslo_log import log

from tobiko.shell.sh import _io
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _process


LOG = log.getLogger(__name__)


def local_execute(command, environment=None, timeout=None, shell=None,
                  stdin=None, stdout=None, stderr=None, expect_exit_status=0,
                  **kwargs):
    """Execute command on local host using local shell"""
    process = local_process(command=command,
                            environment=environment,
                            timeout=timeout,
                            shell=shell,
                            stdin=stdin,
                            stdout=stdout,
                            stderr=stderr,
                            **kwargs)
    return _execute.execute_process(process=process,
                                    stdin=stdin,
                                    expect_exit_status=expect_exit_status)


def local_process(command, environment=None, current_dir=None, timeout=None,
                  shell=None, stdin=None, stdout=None, stderr=True):
    return LocalShellProcessFixture(
        command=command, environment=environment, current_dir=current_dir,
        timeout=timeout, shell=shell, stdin=stdin, stdout=stdout,
        stderr=stderr)


class LocalShellProcessFixture(_process.ShellProcessFixture):

    def create_process(self):
        parameters = self.parameters
        popen_params = {}
        if parameters.stdin:
            popen_params.update(stdin=subprocess.PIPE)
        if parameters.stdout:
            popen_params.update(stdout=subprocess.PIPE)
        if parameters.stderr:
            popen_params.update(stderr=subprocess.PIPE)
        return subprocess.Popen(
            args=self.command,
            bufsize=parameters.buffer_size,
            shell=False,
            cwd=parameters.current_dir,
            env=merge_dictionaries(os.environ, parameters.environment),
            universal_newlines=False,
            **popen_params)

    def setup_stdin(self):
        set_non_blocking(self.process.stdin.fileno())
        self.stdin = _io.ShellStdin(delegate=self.process.stdin,
                              buffer_size=self.parameters.buffer_size)

    def setup_stdout(self):
        set_non_blocking(self.process.stdout.fileno())
        self.stdout = _io.ShellStdout(delegate=self.process.stdout,
                                      buffer_size=self.parameters.buffer_size)

    def setup_stderr(self):
        set_non_blocking(self.process.stderr.fileno())
        self.stderr = _io.ShellStderr(delegate=self.process.stderr,
                                      buffer_size=self.parameters.buffer_size)

    def poll_exit_status(self):
        return self.process.poll()

    def kill(self):
        try:
            self.process.kill()
        except Exception:
            LOG.exception('Failed killing subprocess')

    @property
    def pid(self):
        return self.process.pid


def set_non_blocking(fd):
    flag = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)


def merge_dictionaries(*dictionaries):
    merged = {}
    for d in dictionaries:
        if d:
            merged.update(d)
    return merged
