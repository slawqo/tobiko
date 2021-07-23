# Copyright (c) 2021 Red Hat, Inc.
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
from __future__ import division

import io

import dpkt
from oslo_log import log

from tobiko.shell.tcpdump import _interface
from tobiko.shell.tcpdump import _parameters
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


def start_capture(capture_file: str,
                  interface: str = None,
                  capture_filter: str = None,
                  capture_timeout: int = None,
                  ssh_client: ssh.SSHClientType = None) \
        -> sh.ShellProcessFixture:

    parameters = _parameters.tcpdump_parameters(
        capture_file=capture_file,
        interface=interface,
        capture_filter=capture_filter,
        capture_timeout=capture_timeout)

    command = _interface.get_tcpdump_command(parameters)

    # when ssh_client is None, an ssh session is created on localhost

    # using a process we run a fire and forget tcpdump command
    process = sh.process(command=command,
                         ssh_client=ssh_client,
                         sudo=True)
    process.execute()
    return process


def stop_capture(process):
    process.kill()
    process.close()


def get_pcap(process,
             capture_file: str,
             ssh_client: ssh.SSHClientType = None) -> dpkt.pcap.Reader:
    stop_capture(process)

    stdout = sh.execute(
        f'cat {capture_file}', ssh_client=ssh_client, sudo=True).stdout
    pcap = dpkt.pcap.Reader(io.BytesIO(stdout))
    return pcap
