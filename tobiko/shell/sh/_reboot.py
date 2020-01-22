# Copyright 2019 Red Hat
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
from tobiko.shell.sh import _hostname
from tobiko.shell.sh import _uptime


LOG = log.getLogger(__name__)


class RebootHostTimeoutError(tobiko.TobikoException):
    message = "host {hostname!r} not rebooted after {timeout!s} seconds"


def reboot_host(ssh_client, wait=True, timeout=None, sleep_interval=None,
                retry_interval=None):
    """Gracefully reboots a remote host using an SSH client

    Given an SSH client to a remote host it executes /sbin/reboot command
    and then it start polling for remote host uptime value to make sure
    the node is actually rebooted before a given timeout.
    """

    with ssh_client:
        hostname = _hostname.get_hostname(ssh_client=ssh_client,
                                          timeout=timeout)
        LOG.debug('Rebooting host %r...', hostname)
        _execute.execute('sudo /sbin/reboot', timeout=timeout, stdout=False,
                         ssh_client=ssh_client)

    if wait:
        if timeout is None:
            timeout = 300.
        if sleep_interval is None:
            sleep_interval = 1.
        if retry_interval is None:
            retry_interval = 100.
        else:
            retry_interval = max(retry_interval, 5.)

        start_time = time.time()
        elapsed_time = 0.
        retry_time = retry_interval

        while True:
            try:
                _wait_for_host_rebooted(ssh_client=ssh_client,
                                        hostname=hostname,
                                        start_time=start_time,
                                        timeout=min(retry_time, timeout),
                                        sleep_interval=sleep_interval)
                break

            except RebootHostTimeoutError:
                elapsed_time = time.time() - start_time
                if elapsed_time >= timeout:
                    raise

                LOG.debug("Retrying rebooting host %r %s seconds after "
                          "reboot...", hostname, elapsed_time)
                with ssh_client:
                    _execute.execute('sudo /sbin/reboot', timeout=(
                        timeout - elapsed_time), ssh_client=ssh_client)
                elapsed_time = time.time() - start_time
                retry_time = elapsed_time + retry_interval


def _wait_for_host_rebooted(ssh_client, hostname, start_time, timeout,
                            sleep_interval):
    while not _is_host_rebooted(ssh_client=ssh_client,
                                hostname=hostname,
                                start_time=start_time,
                                timeout=timeout):
        if sleep_interval > 0.:
            time.sleep(sleep_interval)


def _is_host_rebooted(ssh_client, hostname, start_time, timeout):
    # ensure SSH connection is closed before retrying connecting
    tobiko.cleanup_fixture(ssh_client)
    assert ssh_client.client is None

    elapsed_time = time.time() - start_time
    if elapsed_time >= timeout:
        raise RebootHostTimeoutError(hostname=hostname,
                                     timeout=timeout)

    LOG.debug("Reconnecting to host %r %s seconds after reboot...",
              hostname, elapsed_time)
    try:
        uptime = _uptime.get_uptime(ssh_client=ssh_client,
                                    timeout=(timeout-elapsed_time))
    except Exception as ex:
        # if disconnected while getting uptime we assume the VM is just
        # rebooting. These are good news!
        tobiko.cleanup_fixture(ssh_client)
        assert ssh_client.client is None
        elapsed_time = time.time() - start_time
        LOG.debug("Unable to get uptime from %r host after %r "
                  "seconds: %s", hostname, elapsed_time, ex)
        return False

    # verify that reboot actually happened by comparing elapsed time with
    # uptime
    elapsed_time = time.time() - start_time
    if uptime >= elapsed_time:
        tobiko.cleanup_fixture(ssh_client)
        assert ssh_client.client is None
        LOG.warning("Host %r still not rebooted after %s seconds after reboot "
                    "(uptime=%r)", hostname, elapsed_time, uptime)
        return False

    LOG.debug("Reconnected to host %r %s seconds after reboot "
              "(uptime=%r)", hostname, elapsed_time, uptime)
    assert ssh_client.client is not None
    return True
