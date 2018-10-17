# Copyright 2018 Red Hat
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
import os
import re
import signal
import subprocess

from tempest.common.utils import net_utils
from tempest.lib.common.utils import test_utils


def run_background_ping(server_fip):
    """Starts background ping process."""
    ping_log = open("/tmp/ping_%s_output" % server_fip, 'ab')
    p = subprocess.Popen(['ping -q %s' % server_fip],
                         stdout=ping_log, shell=True)
    with open("/tmp/ping_%s_pid" % server_fip, 'ab') as pf:
        pf.write(str(p.pid))


def get_packet_loss(server_fip):
    """Returns packet loss."""

    try:
        # Kill Process
        with open("/tmp/ping_%s_pid" % server_fip) as f:
            pid = f.read()
        os.kill(int(pid), signal.SIGINT)

        # Packet loss pattern
        p = re.compile("(\d{1,3})% packet loss")

        # Get ping package loss
        with open("/tmp/ping_%s_output" % server_fip) as f:
            m = p.search(f.read())
            packet_loss = m.group(1)
    finally:
        # Remove files created by pre test
        os.remove("/tmp/ping_%s_output" % server_fip)
        os.remove("/tmp/ping_%s_pid" % server_fip)

    return packet_loss


def ping_ip_address(ip_address, should_succeed=True,
                    ping_timeout=None, mtu=None):

    timeout = ping_timeout or 120
    cmd = ['ping', '-c1', '-w1']

    if mtu:
        cmd += [
            # don't fragment
            '-M', 'do',
            # ping receives just the size of ICMP payload
            '-s', str(net_utils.get_ping_payload_size(mtu, 4))
        ]
    cmd.append(ip_address)

    def ping():
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.communicate()

        return (proc.returncode == 0) == should_succeed

    result = test_utils.call_until_true(ping, timeout, 1)
    return result
