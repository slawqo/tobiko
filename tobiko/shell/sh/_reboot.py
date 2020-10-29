# Copyright 2020 Red Hat
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

import typing  # noqa

from oslo_log import log

import tobiko
from tobiko.shell.sh import _exception
from tobiko.shell.sh import _uptime
from tobiko.shell import ssh


LOG = log.getLogger(__name__)

hard_reset_method = 'sudo chmod o+w /proc/sysrq-trigger;' \
               'sudo echo b > /proc/sysrq-trigger'

soft_reset_method = 'sudo /sbin/reboot'


class RebootHostError(tobiko.TobikoException):
    message = "host {hostname!r} not rebooted: {cause}"


class RebootHostTimeoutError(RebootHostError):
    message = "host {hostname!r} not rebooted after {timeout!s} seconds"


def reboot_host(ssh_client: ssh.SSHClientFixture, wait: bool = True,
                timeout: tobiko.Seconds = None, method=soft_reset_method):
    reboot = RebootHostOperation(ssh_client=ssh_client, wait=wait,
                                 timeout=timeout, method=method)
    return tobiko.setup_fixture(reboot)


class RebootHostOperation(tobiko.Operation):

    hostname = None
    is_rebooted: typing.Optional[bool] = None
    start_time: tobiko.Seconds = None

    default_wait_timeout = 300.
    default_wait_interval = 5.
    default_wait_count = 60

    @property
    def ssh_client(self) -> ssh.SSHClientFixture:
        if self._ssh_client is None:
            raise ValueError(f"SSH client for object '{self}' is None")
        return self._ssh_client

    def __init__(self,
                 ssh_client: typing.Optional[ssh.SSHClientFixture] = None,
                 wait=True,
                 timeout: tobiko.Seconds = None,
                 method=soft_reset_method):
        super(RebootHostOperation, self).__init__()
        self._ssh_client = ssh_client
        tobiko.check_valid_type(self.ssh_client, ssh.SSHClientFixture)
        self.wait = bool(wait)
        self.timeout = tobiko.to_seconds(timeout)
        self.method = method

    def run_operation(self):
        ssh_client = self.ssh_client
        with ssh_client:
            self.hostname = ssh_client.hostname
            LOG.debug(f"Rebooting host '{self.hostname}'... ")
            self.is_rebooted = False
            self.start_time = tobiko.time()
            try:
                ssh_client.connect(connection_timeout=self.timeout).\
                    exec_command(self.method)
            except _exception.ShellTimeoutExpired as ex:
                LOG.debug(f"Reboot command timeout expired: {ex}")
        if self.wait:
            self.wait_for_operation()

    def cleanup_fixture(self):
        self.is_rebooted = None
        self.hostname = None
        self.start_time = None

    @property
    def elapsed_time(self) -> tobiko.Seconds:
        if self.start_time is None:
            return None
        else:
            return tobiko.time() - self.start_time

    @property
    def time_left(self) -> tobiko.Seconds:
        if self.timeout is None or self.elapsed_time is None:
            return None
        else:
            return self.timeout - self.elapsed_time

    def wait_for_operation(self, timeout: tobiko.Seconds = None):
        if self.is_rebooted:
            return
        try:
            for attempt in tobiko.retry(
                    timeout=tobiko.min_seconds(timeout, self.time_left),
                    default_timeout=self.default_wait_timeout,
                    default_count=self.default_wait_count,
                    default_interval=self.default_wait_interval):
                # ensure SSH connection is closed before retrying connecting
                tobiko.cleanup_fixture(self.ssh_client)
                assert self.ssh_client.client is None
                LOG.debug(f"Getting uptime after reboot '{self.hostname}' "
                          "after reboot... ")
                try:
                    up_time = _uptime.get_uptime(ssh_client=self.ssh_client,
                                                 timeout=30.)

                except Exception:
                    # if disconnected while getting up time we assume the VM is
                    # just rebooting. These are good news!
                    LOG.debug("Unable to get uptime from host "
                              f"'{self.hostname}'", exc_info=1)
                    attempt.check_limits()
                else:

                    # verify that reboot actually happened by comparing elapsed
                    # time with up_time
                    elapsed_time = self.elapsed_time
                    if up_time < elapsed_time:
                        assert self.ssh_client.client is not None
                        self.is_rebooted = True
                        LOG.debug(f"Host '{self.hostname}' restarted "
                                  f"{elapsed_time} seconds after "
                                  f"reboot operation (up_time={up_time})")
                        break
                    else:
                        LOG.debug(f"Host '{self.hostname}' still not "
                                  f"restarted {elapsed_time} seconds after "
                                  f"reboot operation (up_time={up_time!r})")
                        attempt.check_limits()
        finally:
            if not self.is_rebooted:
                try:
                    tobiko.cleanup_fixture(self.ssh_client)
                except Exception:
                    LOG.exception("Error closing SSH connection to "
                                  f"'{self.hostname}'")
