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

import time

from oslo_log import log
import paramiko

import tobiko
from tobiko.shell.sh import _exception
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _io
from tobiko.shell.sh import _local
from tobiko.shell.sh import _process
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


def ssh_execute(ssh_client, command, environment=None, timeout=None,
                stdin=None, stdout=None, stderr=None, shell=None,
                expect_exit_status=0, **kwargs):
    """Execute command on remote host using SSH client"""
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
                ssh_client=None, sudo=None, network_namespace=None):
    if ssh_client is None:
        ssh_client = ssh.ssh_proxy_client()
    if ssh_client:
        return SSHShellProcessFixture(
            command=command, environment=environment, current_dir=current_dir,
            timeout=timeout, shell=shell, stdin=stdin, stdout=stdout,
            stderr=stderr, ssh_client=ssh_client, sudo=sudo,
            network_namespace=network_namespace)
    else:
        return _local.local_process(
            command=command, environment=environment, current_dir=current_dir,
            timeout=timeout, shell=shell, stdin=stdin, stdout=stdout,
            stderr=stderr, sudo=sudo, network_namespace=network_namespace)


class SSHShellProcessParameters(_process.ShellProcessParameters):

    ssh_client = None


class SSHShellProcessFixture(_process.ShellProcessFixture):

    retry_create_process_count = 3
    retry_create_process_intervall = 1.

    def init_parameters(self, **kwargs):
        return SSHShellProcessParameters(**kwargs)

    def create_process(self):
        """Execute command on a remote host using SSH client"""
        command = str(self.command)
        ssh_client = self.ssh_client
        parameters = self.parameters

        tobiko.check_valid_type(ssh_client, ssh.SSHClientFixture)
        tobiko.check_valid_type(parameters, SSHShellProcessParameters)
        environment = parameters.environment

        retry_count = self.retry_create_process_count
        for retry_number in range(1, retry_count + 1):
            timeout = self.timeout and float(self.timeout)
            LOG.debug("Executing remote command: %r (login=%r, timeout=%r, "
                      "environment=%r)...",
                      command, ssh_client.login, timeout, environment or {})
            try:
                return self._try_create_process(command=command,
                                                environment=environment,
                                                ssh_client=ssh_client,
                                                timeout=timeout)
            except paramiko.SSHException as ex:
                try:
                    # Before doing anything else cleanup SSH connection
                    tobiko.cleanup_fixture(ssh_client)
                except Exception:
                    LOG.exception('Failed closing SSH connection')
                if "timeout" in str(ex).lower():
                    LOG.debug('Timed out executing command %r (timeout=%s)',
                              command, timeout, exc_info=1)
                    raise _exception.ShellTimeoutExpired(command=command,
                                                         stdin=None,
                                                         stdout=None,
                                                         stderr=None,
                                                         timeout=timeout)

                LOG.debug('Error creating SSH process (attempt %d of %d)',
                          retry_number, retry_count, exc_info=1)
                if retry_number >= retry_count:
                    # Last attempt has failed!
                    raise
                else:
                    # Be patient, this could help things getting better
                    time.sleep(self.retry_create_process_intervall)

    def _try_create_process(self, command, environment, ssh_client, timeout):
        client = ssh_client.connect()
        process = client.get_transport().open_session(timeout=timeout)
        if environment:
            process.update_environment(environment)
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
        exit_status = getattr(self.process, 'exit_status', None)
        if exit_status and exit_status < 0:
            exit_status = None
        return exit_status

    def _get_exit_status(self, time_left=None):
        process = self.process
        if not process.exit_status_ready():
            # workaround for paramiko timeout problem
            time_left = min(time_left, 120.0)
            # recv_exit_status method doesn't accept timeout parameter
            LOG.debug('Waiting for command (%s) exit status (time_left=%r)',
                      self.command, time_left)
            if not process.status_event.wait(timeout=time_left):
                LOG.debug('Timed out before status event being set')

        if process.exit_status >= 0:
            return process.exit_status
        else:
            return None

    def kill(self):
        process = self.process
        LOG.debug('Killing remote process: %r', self.command)
        try:
            process.close()
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
