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
from __future__ import division

import typing

import netaddr
from oslo_log import log

import tobiko
from tobiko import config
from tobiko.shell.iperf3 import _execute
from tobiko.shell import ssh


CONF = config.CONF
LOG = log.getLogger(__name__)


def assert_has_bandwith_limits(
        address: typing.Union[str, netaddr.IPAddress],
        min_bandwith: float,
        max_bandwith: float,
        bitrate: int = None,
        download: bool = None,
        port: int = None,
        protocol: str = None,
        ssh_client: ssh.SSHClientType = None,
        timeout: tobiko.Seconds = None) -> None:
    bandwith = _execute.get_bandwidth(address=address,
                                      bitrate=bitrate,
                                      download=download,
                                      port=port,
                                      protocol=protocol,
                                      ssh_client=ssh_client,
                                      timeout=timeout)
    testcase = tobiko.get_test_case()
    LOG.debug(f'measured bandwith: {bandwith}')
    LOG.debug(f'bandwith limits: {min_bandwith} ... {max_bandwith}')
    # an 8% of lower deviation is allowed
    testcase.assertGreater(bandwith, min_bandwith)
    # a 5% of upper deviation is allowed
    testcase.assertLess(bandwith, max_bandwith)
