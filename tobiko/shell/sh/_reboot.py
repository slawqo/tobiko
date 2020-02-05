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

import time

from oslo_log import log

import tobiko
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _uptime
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


class RebootHostTimeoutError(tobiko.TobikoException):
    message = "host {hostname!r} not rebooted after {timeout!s} seconds"


def reboot_host(ssh_client, wait=True, timeout=None, sleep_interval=None):
    reboot = RebootHostOperation(ssh_client=ssh_client,
                                 wait=wait,
                                 timeout=timeout,
                                 sleep_interval=sleep_interval)
    return tobiko.setup_fixture(reboot)


class RebootHostOperation(tobiko.Operation):

    wait = True
    start_time = None
    hostname = None
    timeout = 600.
    ssh_client = None
    sleep_interval = 1.
    is_rebooted = False

    def __init__(self, ssh_client=None, timeout=None, wait=None,
                 sleep_interval=None):
        super(RebootHostOperation, self).__init__()
        if ssh_client:
            self.ssh_client = ssh_client
        tobiko.check_valid_type(self.ssh_client, ssh.SSHClientFixture)

        if timeout is not None:
            self.timeout = float(timeout)
        assert self.timeout > 0.

        if wait is not None:
            self.wait = bool(wait)

        if sleep_interval is not None:
            self.sleep_interval = float(sleep_interval)
        assert self.sleep_interval >= 0.

    def run_operation(self):
        self.start_time = time.time()
        ssh_client = self.ssh_client
        with ssh_client:
            self.is_rebooted = False
            self.hostname = hostname = ssh_client.hostname
            LOG.debug('Rebooting host %r...', hostname)
            _execute.execute('sudo /sbin/reboot', timeout=self.timeout,
                             stdout=False, ssh_client=ssh_client)
        if self.wait:
            self.wait_for_operation()

    def cleanup_fixture(self):
        if self.hostname is not None:
            del self.hostname
        if self.start_time is not None:
            del self.start_time
        self.is_rebooted = False

    def wait_for_operation(self):
        sleep_interval = self.sleep_interval
        while not self.check_is_rebooted():
            if sleep_interval > 0.:
                time.sleep(sleep_interval)

    def check_is_rebooted(self):
        if self.is_rebooted:
            return True

        # ensure SSH connection is closed before retrying connecting
        ssh_client = self.ssh_client
        tobiko.cleanup_fixture(ssh_client)
        assert ssh_client.client is None

        elapsed_time = self.check_elapsed_time()
        LOG.debug("Reconnecting to host %r %s seconds after reboot...",
                  self.hostname, elapsed_time)
        if elapsed_time is None:
            raise RuntimeError("Reboot operation didn't started")

        try:
            uptime = _uptime.get_uptime(ssh_client=ssh_client,
                                        timeout=(self.timeout-elapsed_time))
        except Exception:
            # if disconnected while getting uptime we assume the VM is just
            # rebooting. These are good news!
            tobiko.cleanup_fixture(ssh_client)
            assert ssh_client.client is None
            LOG.debug("Unable to get uptime from host %r", self.hostname,
                      exc_info=1)
            return False

        # verify that reboot actually happened by comparing elapsed time with
        # uptime
        elapsed_time = self.get_elapsed_time()
        if uptime >= elapsed_time:
            tobiko.cleanup_fixture(ssh_client)
            assert ssh_client.client is None
            LOG.warning("Host %r still not restarted %s seconds after "
                        "reboot operation (uptime=%r)", self.hostname,
                        elapsed_time, uptime)
            return False

        self.is_rebooted = True
        LOG.debug("Host %r resterted %s seconds after reboot operation"
                  "(uptime=%r)", self.hostname, elapsed_time - uptime, uptime)
        assert ssh_client.client is not None
        return True

    def check_elapsed_time(self):
        elapsed_time = self.get_elapsed_time()
        if elapsed_time is None:
            return None
        if elapsed_time >= self.timeout:
            raise RebootHostTimeoutError(hostname=self.hostname,
                                         timeout=self.timeout)
        return elapsed_time

    def get_elapsed_time(self):
        start_time = self.start_time
        if start_time is None:
            return None
        return time.time() - start_time
