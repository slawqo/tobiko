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

import io
import time

from oslo_log import log

import tobiko

from tobiko.shell.sh import _command
from tobiko.shell.sh import _exception
from tobiko.shell.sh import _io


LOG = log.getLogger(__name__)


def process(command=None, environment=None, timeout=None, shell=None,
            stdin=None, stdout=None, stderr=None, ssh_client=None, **kwargs):
    kwargs.update(command=command, environment=environment, timeout=timeout,
                  shell=shell, stdin=stdin, stdout=stdout, stderr=stderr)
    try:
        from tobiko.shell.sh import _ssh
        from tobiko.shell import ssh
    except ImportError:
        if ssh_client:
            raise
    else:
        if ssh_client is None:
            ssh_client = ssh.ssh_proxy_client()
        if ssh_client:
            return _ssh.ssh_process(ssh_client=ssh_client, **kwargs)

    from tobiko.shell.sh import _local
    return _local.local_process(**kwargs)


class Parameters(object):

    def __init__(self, **kwargs):
        cls = type(self)
        for name, value in kwargs.items():
            if value is not None:
                if not hasattr(cls, name):
                    raise ValueError('Invalid parameter: {!s}'.format(name))
                setattr(self, name, value)


class ShellProcessParameters(Parameters):

    command = None
    environment = None
    current_dir = None
    timeout = None
    shell = None
    stdin = False
    stdout = True
    stderr = True
    buffer_size = io.DEFAULT_BUFFER_SIZE
    poll_interval = 1.


class ShellProcessFixture(tobiko.SharedFixture):

    parameters = None
    command = None
    timeout = None
    process = None
    stdin = None
    stdout = None
    stderr = None

    def __init__(self, **kwargs):
        super(ShellProcessFixture, self).__init__()
        self.parameters = self.init_parameters(**kwargs)

    def init_parameters(self, **kwargs):
        return ShellProcessParameters(**kwargs)

    def execute(self):
        return tobiko.setup_fixture(self)

    def setup_fixture(self):
        parameters = self.parameters

        self.setup_command()
        if parameters.timeout:
            self.setup_timeout()

        self.setup_process()

        if parameters.stdin:
            self.setup_stdin()
        if parameters.stdout:
            self.setup_stdout()
        if parameters.stderr:
            self.setup_stderr()

    def setup_command(self):
        command = _command.shell_command(self.parameters.command)
        shell = self.parameters.shell
        if shell:
            if shell is True:
                shell = default_shell_command()
            else:
                shell = _command.shell_command(shell)
            command = shell + [str(command)]
        else:
            command = _command.shell_command(command)
        self.command = command

    def setup_timeout(self):
        self.timeout = ShellProcessTimeout(self.parameters.timeout)

    def setup_process(self):
        self.process = self.create_process()
        self.addCleanup(self.close)

    def setup_stdin(self):
        raise NotImplementedError

    def setup_stdout(self):
        raise NotImplementedError

    def setup_stderr(self):
        raise NotImplementedError

    def create_process(self):
        raise NotImplementedError

    def close_stdin(self):
        stdin = self.stdin
        if stdin is not None:
            try:
                stdin.closed or stdin.close()
            except Exception:
                LOG.exception("Error closing STDIN stream: %r", self.stdin)

    def close_stdout(self):
        stdout = self.stdout
        if stdout is not None:
            try:
                stdout.closed or stdout.close()
            except Exception:
                LOG.exception("Error closing STDOUT stream: %r", self.stdout)

    def close_stderr(self):
        stderr = self.stderr
        if stderr is not None:
            try:
                stderr.closed or stderr.close()
            except Exception:
                LOG.exception("Error closing STDERR stream: %r", self.stderr)

    def close(self, timeout=None):
        self.close_stdin()
        try:
            # Drain all incoming data from STDOUT and STDERR
            self.wait(timeout=timeout)
        finally:
            # Avoid leaving zombie processes
            self.timeout = None
            self.close_stdout()
            self.close_stderr()
            if self.is_running:
                self.kill()

    def __getattr__(self, name):
        try:
            # Get attributes from parameters class
            return getattr(self.parameters, name)
        except AttributeError:
            message = "object {!r} has not attribute {!r}".format(self, name)
            raise AttributeError(message)

    def kill(self):
        raise NotImplementedError

    def poll_exit_status(self):
        raise NotImplementedError

    @property
    def exit_status(self):
        return self.poll_exit_status()

    @property
    def is_running(self):
        return self.exit_status is None

    def check_is_running(self):
        exit_status = self.poll_exit_status()
        if exit_status is not None:
            raise _exception.ShellProcessTeriminated(
                command=str(self.command),
                exit_status=int(exit_status),
                stdin=str_from_stream(self.stdin),
                stdout=str_from_stream(self.stdout),
                stderr=str_from_stream(self.stderr))

    def check_stdin_is_opened(self):
        if self.stdin.closed:
            raise _exception.ShellStdinClosed(
                command=str(self.command),
                stdin=str_from_stream(self.stdin),
                stdout=str_from_stream(self.stdout),
                stderr=str_from_stream(self.stderr))

    def send(self, data, timeout=None):
        self.comunicate(stdin=data, timeout=timeout, wait=False)

    def wait(self, timeout=None):
        self.comunicate(stdin=None, timeout=timeout, wait=True)

    def comunicate(self, stdin=None, stdout=True, stderr=True, timeout=None,
                   wait=True, buffer_size=None):
        timeout = ShellProcessTimeout(timeout=timeout)
        # Avoid waiting for data in the first loop
        poll_interval = 0.
        poll_files = _io.select_opened_files([stdin and self.stdin,
                                              stdout and self.stdout,
                                              stderr and self.stderr])
        while wait or stdin:
            self.check_timeout(timeout=timeout)
            wait = wait and (poll_files or self.is_running)
            read_ready, write_ready = _io.select_files(files=poll_files,
                                                       timeout=poll_interval)
            if read_ready or write_ready:
                # Avoid waiting for data the next time
                poll_interval = 0.
                if self.stdin in write_ready:
                    # Write data to remote STDIN
                    stdin = self._write_to_stdin(stdin)
                    if not stdin:
                        if wait:
                            self.stdin.close()
                        else:
                            # Stop polling STDIN for write
                            self.stdin.flush()
                            poll_files.remove(self.stdin)
                if self.stdout in read_ready:
                    # Read data from remote STDOUT
                    self._read_from_stdout(buffer_size=buffer_size)
                if self.stderr in read_ready:
                    # Read data from remote STDERR
                    self._read_from_stderr(buffer_size=buffer_size)
            else:
                # Wait for data in the following loops
                poll_interval = min(self.poll_interval,
                                    self.check_timeout(timeout=timeout))
            # Remove closed streams
            poll_files = _io.select_opened_files(poll_files)

    def _write_to_stdin(self, data, check=True):
        """Write data to STDIN"""
        if check:
            self.check_stdin_is_opened()
        sent_bytes = self.stdin.write(data)
        if sent_bytes:
            return data[sent_bytes:] or None
        else:
            LOG.debug("%r closed by peer on %r", self.stdin, self)
            self.stdin.close()

    def _read_from_stdout(self, buffer_size=None):
        """Read data from remote stream"""
        # Read data from remote stream
        chunk = self.stdout.read(buffer_size)
        if chunk:
            return chunk
        else:
            LOG.debug("%r closed by peer on %r", self.stdout, self)
            self.stdout.close()
            return None

    def _read_from_stderr(self, buffer_size=None):
        """Read data from remote stream"""
        # Read data from remote stream
        chunk = self.stderr.read(buffer_size)
        if chunk:
            return chunk
        else:
            LOG.debug("%r closed by peer on %r", self.stderr, self)
            self.stderr.close()
            return None

    def time_left(self, now=None, timeout=None):
        now = now or time.time()
        time_left = self.timeout.time_left(now=now)
        if timeout:
            time_left = min(time_left, timeout.time_left(now=now))
        return time_left

    def check_timeout(self, timeout=None, now=None):
        now = now or time.time()
        time_left = float('inf')
        for timeout in [self.timeout, timeout]:
            if timeout is not None:
                time_left = min(time_left, timeout.time_left(now=now))
                if time_left <= 0.:
                    ex = _exception.ShellTimeoutExpired(
                        command=str(self.command),
                        timeout=timeout.timeout,
                        stdin=str_from_stream(self.stdin),
                        stdout=str_from_stream(self.stdout),
                        stderr=str_from_stream(self.stderr))
                    LOG.debug("%s", ex)
                    raise ex
        return time_left

    def check_exit_status(self, expected_status=0):
        exit_status = self.poll_exit_status()
        if exit_status is None:
            time_left = self.check_timeout()
            ex = _exception.ShellProcessNotTeriminated(
                command=str(self.command),
                time_left=time_left,
                stdin=self.stdin,
                stdout=self.stdout,
                stderr=self.stderr)
            LOG.debug("%s", ex)
            raise ex

        exit_status = int(exit_status)
        if expected_status != exit_status:
            ex = _exception.ShellCommandFailed(
                command=str(self.command),
                exit_status=exit_status,
                stdin=str_from_stream(self.stdin),
                stdout=str_from_stream(self.stdout),
                stderr=str_from_stream(self.stderr))
            LOG.debug("%s", ex)
            raise ex

        LOG.debug("Command '%s' succeeded (exit_status=%d):\n"
                  "stdin:\n%s\n"
                  "stdout:\n%s\n"
                  "stderr:\n%s",
                  self.command, exit_status,
                  self.stdin, self.stdout, self.stderr)


def merge_dictionaries(*dictionaries):
    merged = {}
    for d in dictionaries:
        if d:
            merged.update(d)
    return merged


class ShellProcessTimeout(object):

    timeout = float('inf')

    def __init__(self, timeout=None, start_time=None):
        if timeout is None:
            timeout = float('inf')
        else:
            timeout = float(timeout)
        self.timeout = timeout
        start_time = start_time and float(start_time) or time.time()
        self.start_time = start_time
        self.end_time = start_time + timeout

    def __float__(self):
        return self.timeout

    def time_left(self, now=None):
        now = now or time.time()
        return self.end_time - now

    def is_expired(self, now=None):
        raise self.time_left(now=now) <= 0.


def str_from_stream(stream):
    if stream is not None:
        return str(stream)
    else:
        return None


def default_shell_command():
    from tobiko import config
    CONF = config.CONF
    return _command.shell_command(CONF.tobiko.shell.command)
