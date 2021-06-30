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

import json
import typing

import netaddr
from oslo_log import log

import tobiko
from tobiko.shell.iperf3 import _interface
from tobiko.shell.iperf3 import _parameters
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


def get_bandwidth(address: typing.Union[str, netaddr.IPAddress],
                  bitrate: int = None,
                  download: bool = None,
                  port: int = None,
                  protocol: str = None,
                  ssh_client: ssh.SSHClientType = None,
                  timeout: tobiko.Seconds = None) -> float:
    iperf_measures = execute_iperf3_client(address=address,
                                           bitrate=bitrate,
                                           download=download,
                                           port=port,
                                           protocol=protocol,
                                           ssh_client=ssh_client,
                                           timeout=timeout)
    return calculate_bandwith(iperf_measures)


def calculate_bandwith(iperf_measures) -> float:
    # first interval is removed because BW measured during it is not
    # limited - it takes ~ 1 second to traffic shaping algorithm to apply
    # bw limit properly (buffer is empty when traffic starts being sent)
    intervals = iperf_measures['intervals'][1:]
    bits_received = sum([interval['sum']['bytes'] * 8
                         for interval in intervals])
    elapsed_time = sum([interval['sum']['seconds']
                        for interval in intervals])
    # bw in bits per second
    return bits_received / elapsed_time


def execute_iperf3_client(address: typing.Union[str, netaddr.IPAddress],
                          bitrate: int = None,
                          download: bool = None,
                          port: int = None,
                          protocol: str = None,
                          ssh_client: ssh.SSHClientType = None,
                          timeout: tobiko.Seconds = None) \
        -> typing.Dict:
    params_timeout: typing.Optional[int] = None
    if timeout is not None:
        params_timeout = int(timeout - 0.5)
    parameters = _parameters.iperf3_client_parameters(address=address,
                                                      bitrate=bitrate,
                                                      download=download,
                                                      port=port,
                                                      protocol=protocol,
                                                      timeout=params_timeout)
    command = _interface.get_iperf3_client_command(parameters)

    # output is a dictionary
    output = sh.execute(command,
                        ssh_client=ssh_client,
                        timeout=timeout).stdout
    return json.loads(output)
