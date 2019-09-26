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
import sys
import time

from oslo_log import log

import tobiko
from tobiko.shell.sh import _io
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _path
from tobiko.shell.sh import _process


LOG = log.getLogger(__name__)


TimeoutExpired = getattr(subprocess, 'TimeoutExpired', None)


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


class LocalExecutePathFixture(_path.ExecutePathFixture):

    executable_dirs = [os.path.realpath(os.path.join(d, 'bin'))
                       for d in [sys.prefix, sys.exec_prefix]]
    environ = os.environ


class LocalShellProcessFixture(_process.ShellProcessFixture):

    path_execute = tobiko.required_fixture(LocalExecutePathFixture)

    def create_process(self):
        tobiko.setup_fixture(self.path_execute)
        parameters = self.parameters
        args = self.command
        stdin = parameters.stdin and subprocess.PIPE or None
        stdout = parameters.stdout and subprocess.PIPE or None
        stderr = parameters.stderr and subprocess.PIPE or None
        env = merge_dictionaries(os.environ, parameters.environment)
        return subprocess.Popen(args=args,
                                bufsize=parameters.buffer_size,
                                shell=False,
                                universal_newlines=False,
                                env=env,
                                cwd=parameters.current_dir,
                                stdin=stdin,
                                stdout=stdout,
                                stderr=stderr)

    def setup_stdin(self):
        self.stdin = _io.ShellStdin(delegate=self.process.stdin,
                                    buffer_size=self.parameters.buffer_size)

    def setup_stdout(self):
        self.stdout = _io.ShellStdout(delegate=self.process.stdout,
                                      buffer_size=self.parameters.buffer_size)

    def setup_stderr(self):
        set_non_blocking(self.process.stderr.fileno())
        self.stderr = _io.ShellStderr(delegate=self.process.stderr,
                                      buffer_size=self.parameters.buffer_size)

    def poll_exit_status(self):
        return self.process.poll()

    if TimeoutExpired is None:
        # Workaround for old Python versions
        def _get_exit_status(self, time_left):
            start_time = now = time.time()
            end_time = start_time + time_left
            exit_status = self.poll_exit_status()
            while exit_status is None and now < end_time:
                time.sleep(0.1)
                exit_status = self.poll_exit_status()
                now = time.time()
            return exit_status
    else:
        def _get_exit_status(self, time_left):
            try:
                exit_status = self.process.wait(timeout=time_left)
            except TimeoutExpired:
                LOG.exception("Failed waiting for subprocess termination")
                return None
            else:
                assert exit_status is not None
                return exit_status

    def kill(self):
        process = self.process
        LOG.debug('Killing local process: %r', self.command)
        try:
            process.kill()
        except Exception:
            LOG.exception('Failed killing local process: %r (PID=%r)',
                          self.command, self.pid)
        else:
            LOG.debug('Local process killed: %r (PID=%r)', self.command,
                      self.pid)

    @property
    def pid(self):
        process = self.process
        return process and process.pid or None


def set_non_blocking(fd):
    flag = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)


def merge_dictionaries(*dictionaries):
    merged = {}
    for d in dictionaries:
        if d:
            merged.update(d)
    return merged
