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

from tobiko.shell.tcpdump import _parameters


def get_tcpdump_command(parameters: _parameters.TcpdumpParameters):
    interface = TcpdumpInterface()
    return interface.get_tcpdump_command(parameters)


class TcpdumpInterface:

    def get_tcpdump_command(
            self, parameters: _parameters.TcpdumpParameters) -> str:
        command = 'tcpdump -s0 -Un'
        if parameters.capture_timeout is not None:
            command = f'timeout {parameters.capture_timeout} ' + command
        options = self.get_tcpdump_options(parameters=parameters)
        return command + ' ' + options

    def get_tcpdump_options(
            self,
            parameters: _parameters.TcpdumpParameters) -> str:
        options = f'-w {parameters.capture_file}'
        if parameters.interface is not None:
            options += f' -i {parameters.interface}'
        else:
            options += ' -i any'
        if parameters.capture_filter is not None:
            options += f' {parameters.capture_filter}'
        return options
