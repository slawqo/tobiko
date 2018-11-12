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
import glob
import inspect
import os
import re
import signal
import subprocess

from tempest.common.utils import net_utils
from tempest.lib.common.utils import test_utils

import tobiko.common.utils.process as proc_utils

SG_RULES = {'ALLOW_ICMP':
            {'direction': 'ingress',
             'protocol': 'icmp'
             }
            }


def run_background_ping(ip):
    """Starts background ping process."""
    # The caller function name
    caller_f = inspect.stack()[1][1].split('/')[-1].split(".py")[0]
    PING_OUTPUT_F = "/tmp/ping_%s_%s_output" % (ip, caller_f)
    PING_PID_F = "/tmp/ping_%s_%s_pid" % (ip, caller_f)
    PING_CMD = 'ping -q %s' % ip

    # Kill any existing running ping process to the same IP address
    if os.path.exists(PING_OUTPUT_F):
        proc_utils.kill_process(pid_f=PING_PID_F)
        for f in glob.glob("/tmp/ping_%s_%s*" % (ip, caller_f)):
            os.remove(f)
        for f in glob.glob("/tmp/ping_%s_%s.*"):
            os.remove(f)

    ping_log = open(PING_OUTPUT_F, 'ab')
    p = subprocess.Popen([PING_CMD], stdout=ping_log, shell=True)
    with open(PING_PID_F, 'ab') as pf:
        pf.write(str(p.pid))


def get_packet_loss(ip):
    """Returns packet loss."""

    # The caller function name
    caller_f = inspect.stack()[1][1].split('/')[-1].split(".py")[0]
    PING_OUTPUT_F = "/tmp/ping_%s_%s_output" % (ip, caller_f)
    PING_PID_F = "/tmp/ping_%s_%s_pid" % (ip, caller_f)

    try:
        # Kill Process
        with open(PING_PID_F) as f:
            pid = f.read()
        os.kill(int(pid), signal.SIGINT)

        # Packet loss pattern
        p = re.compile("(\d{1,3})% packet loss")

        # Get ping package loss
        with open(PING_OUTPUT_F) as f:
            m = p.search(f.read())
            packet_loss = m.group(1)
    finally:
        # Remove files created by pre test

        from shutil import copyfile
        copyfile(PING_OUTPUT_F, "/home/abregman/stam")
        os.remove(PING_OUTPUT_F)
        os.remove(PING_PID_F)

    return packet_loss


def ping_ip_address(ip_address, should_succeed=True,
                    ping_timeout=None, mtu=None):

    timeout = ping_timeout or 10
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
