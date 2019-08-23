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
import paramiko

from tobiko.shell.sh import _io
from tobiko.shell.sh import _local
from tobiko.shell.sh import _process
from tobiko.shell.sh import _execute
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


def ssh_execute(ssh_client, command, environment=None, timeout=None,
                stdin=None, stdout=None, stderr=None, shell=None,
                expect_exit_status=0, **kwargs):
    """Execute command on local host using local shell"""
    process = ssh_process(command=command,
                          environment=environment,
                          timeout=timeout,
                          shell=shell,
                          stdin=stdin,
                          stdout=stdout,
                          stderr=stderr,
                          ssh_client=ssh_client,
                          **kwargs)
    return _execute.execute_process(process=process,
                                    stdin=stdin,
                                    expect_exit_status=expect_exit_status)


def ssh_process(command, environment=None, current_dir=None, timeout=None,
                shell=None, stdin=None, stdout=None, stderr=None,
                ssh_client=None):
    if ssh_client is None:
        ssh_client = ssh.ssh_proxy_client()
    if ssh_client:
        return SSHShellProcessFixture(
            command=command, environment=environment, current_dir=current_dir,
            timeout=timeout, shell=shell, stdin=stdin, stdout=stdout,
            stderr=stderr, ssh_client=ssh_client)
    else:
        return _local.local_process(
            command=command, environment=environment, current_dir=current_dir,
            timeout=timeout, shell=shell, stdin=stdin, stdout=stdout,
            stderr=stderr)


class SSHShellProcessParameters(_process.ShellProcessParameters):

    ssh_client = None


class SSHShellProcessFixture(_process.ShellProcessFixture):

    def init_parameters(self, **kwargs):
        return SSHShellProcessParameters(**kwargs)

    def create_process(self):
        """Execute command on a remote host using SSH client"""
        parameters = self.parameters
        assert isinstance(parameters, SSHShellProcessParameters)

        ssh_client = self.ssh_client
        if isinstance(ssh_client, ssh.SSHClientFixture):
            # Connect to SSH server
            ssh_client = ssh_client.connect()
        process = ssh_client.get_transport().open_session()

        command = str(self.command)
        LOG.debug("Execute command %r on remote host (timeout=%r)...",
                  command, self.timeout)
        if parameters.environment:
            process.update_environment(parameters.environment)
        process.exec_command(command)
        return process

    def setup_stdin(self):
        self.stdin = _io.ShellStdin(
            delegate=StdinSSHChannelFile(self.process, 'wb'),
            buffer_size=self.parameters.buffer_size)

    def setup_stdout(self):
        self.stdout = _io.ShellStdout(
            delegate=StdoutSSHChannelFile(self.process, 'rb'),
            buffer_size=self.parameters.buffer_size)

    def setup_stderr(self):
        self.stderr = _io.ShellStderr(
            delegate=StderrSSHChannelFile(self.process, 'rb'),
            buffer_size=self.parameters.buffer_size)

    def poll_exit_status(self):
        process = self.process
        exit_status = process.exit_status
        if exit_status < 0:
            exit_status = None
        return exit_status

    def get_exit_status(self, timeout=None):
        process = self.process
        exit_status = process.exit_status
        if exit_status < 0:
            timeout = self.check_timeout(timeout=timeout)
            LOG.debug("Waiting for remote command termination: "
                      "timeout=%r, command=%r", timeout, self.command)
            process.status_event.wait(timeout=timeout)
            assert process.status_event.is_set()
            exit_status = process.exit_status
            if exit_status < 0:
                exit_status = None
        return exit_status

    def kill(self):
        process = self.process
        LOG.debug('Killing remote process: %r', self.command)
        try:
            process.kill()
        except Exception:
            LOG.exception("Failed killing remote process: %r",
                          self.command)


class SSHChannelFile(paramiko.ChannelFile):

    def fileno(self):
        return self.channel.fileno()


class StdinSSHChannelFile(SSHChannelFile):

    def close(self):
        super(StdinSSHChannelFile, self).close()
        self.channel.shutdown_write()

    @property
    def write_ready(self):
        return self.channel.send_ready()


class StdoutSSHChannelFile(SSHChannelFile):

    def fileno(self):
        return self.channel.fileno()

    def close(self):
        super(StdoutSSHChannelFile, self).close()
        self.channel.shutdown_read()

    @property
    def read_ready(self):
        return self.channel.recv_ready()


class StderrSSHChannelFile(SSHChannelFile, paramiko.channel.ChannelStderrFile):

    def fileno(self):
        return self.channel.fileno()

    @property
    def read_ready(self):
        return self.channel.recv_stderr_ready()
