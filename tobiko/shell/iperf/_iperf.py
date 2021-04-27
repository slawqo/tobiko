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

import json
import time

from oslo_log import log

from tobiko.shell.iperf import _interface
from tobiko.shell.iperf import _parameters
from tobiko.shell import sh


LOG = log.getLogger(__name__)


def iperf(ssh_client, ssh_server, **iperf_params):
    """Run iperf on both client and server machines and return obtained
    statistics

    :param ssh_client: ssh connection to client
    :param ssh_server: ssh connection to server
    :param **iperf_params: parameters to be forwarded to get_statistics()
        function
    :returns: dict
    """
    parameters_server = _parameters.get_iperf_parameters(
        mode='server', **iperf_params)
    # no output expected
    execute_iperf_server(parameters_server, ssh_server)

    time.sleep(0.1)
    parameters_client = _parameters.get_iperf_parameters(
        mode='client', ip=ssh_server.host, **iperf_params)
    # output is a dictionary
    output = execute_iperf_client(parameters_client, ssh_client)

    return output


def execute_iperf_server(parameters, ssh_client):
    # kill any iperf3 process running before executing it again
    sh.execute(command='pkill iperf3',
               ssh_client=ssh_client,
               expect_exit_status=None)
    time.sleep(1)

    # server is executed in background and no output is expected
    command = _interface.get_iperf_command(parameters=parameters,
                                           ssh_client=ssh_client)
    sh.execute(command=command, ssh_client=ssh_client)


def execute_iperf_client(parameters, ssh_client):
    command = _interface.get_iperf_command(parameters=parameters,
                                           ssh_client=ssh_client)
    result = sh.execute(command=command,
                        ssh_client=ssh_client,
                        timeout=parameters.timeout + 5.)
    return json.loads(result.stdout)
