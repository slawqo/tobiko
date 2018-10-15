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


def run_background_ping(server_fip):
    """Starts background ping process."""
    ping_log = open("/tmp/ping_%s_output" % server_fip, 'ab')
    p = subprocess.Popen(['ping -q %s' % server_fip],
                         stdout=ping_log, shell=True)
    with open("/tmp/ping_%s_pid" % server_fip, 'ab') as pf:
        pf.write(str(p.pid))


def get_packet_loss(server_fip):
    """Returns packet loss."""

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

    # Remove files created by pre test
    os.remove("/tmp/ping_%s_output" % server_fip)
    os.remove("/tmp/ping_%s_pid" % server_fip)

    return packet_loss
