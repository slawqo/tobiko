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

from oslo_log import log

import tobiko
from tobiko.shell import sh


LOG = log.getLogger(__name__)


def install_iperf(ssh_client):
    def iperf_help():
        cmd = 'iperf3 --help'
        try:
            return sh.execute(cmd,
                              expect_exit_status=None,
                              ssh_client=ssh_client)
        except FileNotFoundError:
            return sh.execute_result(command=cmd,
                                     exit_status=127,
                                     stdout='command not found')
    result = iperf_help()
    usage = ((result.stdout and str(result.stdout)) or
             (result.stderr and str(result.stderr)) or "").strip()
    if result.exit_status != 0 and 'command not found' in usage.lower():
        install_command = '{install_tool} install -y iperf3'
        install_tools = ('yum', 'apt')
        for install_tool in install_tools:
            try:
                result = sh.execute(
                    command=install_command.format(install_tool=install_tool),
                    ssh_client=ssh_client,
                    sudo=True)
            except sh.ShellError:
                LOG.debug(f'Unable to install iperf3 using {install_tool}')
            else:
                LOG.debug(f'iperf3 successfully installed with {install_tool}')
                break

        if iperf_help().exit_status != 0:
            raise RuntimeError('iperf3 command was not installed successfully')
    elif result.exit_status != 0:
        raise RuntimeError('Error executing iperf3 command')
    else:
        LOG.debug('iperf3 already installed')


def get_iperf_command(parameters, ssh_client):
    interface = get_iperf_interface(ssh_client=ssh_client)
    return interface.get_iperf_command(parameters)


def get_iperf_interface(ssh_client):
    manager = tobiko.setup_fixture(IperfInterfaceManager)
    interface = manager.get_iperf_interface(ssh_client=ssh_client)
    tobiko.check_valid_type(interface, IperfInterface)
    return interface


class IperfInterfaceManager(tobiko.SharedFixture):
    def __init__(self):
        super(IperfInterfaceManager, self).__init__()
        self.client_interfaces = {}
        self.interfaces = []
        self.default_interface = IperfInterface()

    def add_iperf_interface(self, interface):
        LOG.debug('Register iperf interface %r', interface)
        self.interfaces.append(interface)

    def get_iperf_interface(self, ssh_client):
        try:
            return self.client_interfaces[ssh_client]
        except KeyError:
            pass

        install_iperf(ssh_client)
        LOG.debug('Assign default iperf interface to SSH client %r',
                  ssh_client)
        self.client_interfaces[ssh_client] = self.default_interface
        return self.default_interface


class IperfInterface(object):
    def get_iperf_command(self, parameters):
        command = sh.shell_command(['iperf3'] +
                                   self.get_iperf_options(parameters))
        LOG.debug(f'Got iperf command: {command}')
        return command

    def get_iperf_options(self, parameters):
        options = []

        port = parameters.port
        if port:
            options += self.get_port_option(port)

        timeout = parameters.timeout
        if timeout and parameters.mode == 'client':
            options += self.get_timeout_option(timeout)

        output_format = parameters.output_format
        if output_format:
            options += self.get_output_format_option(output_format)

        bitrate = parameters.bitrate
        if bitrate and parameters.mode == 'client':
            options += self.get_bitrate_option(bitrate)

        download = parameters.download
        if download and parameters.mode == 'client':
            options += self.get_download_option(download)

        protocol = parameters.protocol
        if protocol and parameters.mode == 'client':
            options += self.get_protocol_option(protocol)

        options += self.get_mode_option(parameters)

        return options

    @staticmethod
    def get_mode_option(parameters):
        mode = parameters.mode
        if not mode or mode not in ('client', 'server'):
            raise ValueError('iperf mode values allowed: [client|server]')
        elif mode == 'client' and not parameters.ip:
            raise ValueError('iperf client mode requires a destination '
                             'IP address')
        elif mode == 'client':
            return ['-c', parameters.ip]
        else:  # mode == 'server'
            return ['-s', '-D']  # server mode is executed with daemon mode

    @staticmethod
    def get_download_option(download):
        if download:
            return ['-R']
        else:
            return []

    @staticmethod
    def get_protocol_option(protocol):
        if protocol == 'tcp':
            return []
        elif protocol == 'udp':
            return ['-u']
        else:
            raise ValueError('iperf protocol values allowed: [tcp|udp]')

    @staticmethod
    def get_timeout_option(timeout):
        return ['-t', timeout]

    @staticmethod
    def get_output_format_option(output_format):
        if output_format == 'json':
            return ['-J']
        else:
            raise ValueError('iperf output format values allowed: '
                             '[json]')

    @staticmethod
    def get_port_option(port):
        return ['-p', port]

    @staticmethod
    def get_bitrate_option(bitrate):
        return ['-b', bitrate]
