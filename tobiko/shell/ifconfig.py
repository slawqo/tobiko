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

import netaddr

import tobiko
from tobiko.shell import sh


class IfconfigError(tobiko.TobikoException):
    message = "Unable to get IP addresses from host: {error!s}"


INETS = {
    4: ['inet'],
    6: ['inet6'],
    None: ['inet', 'inet6']
}


def list_ip_addresses(ip_version=None, **execute_params):
    inets = INETS.get(ip_version)
    if inets is None:
        error = "invalid IP version: {!r}".format(ip_version)
        raise IfconfigError(error=error)

    output = execute_ifconfig(**execute_params)

    ips = tobiko.Selection()
    for line in output.splitlines():
        if line.startswith(' '):
            try:
                fields = line.strip().split()
                if fields[0] in inets:
                    address = fields[1]
                    if address.startswith('addr:'):
                        address = address[len('addr:'):]
                        if not address:
                            address = fields[2]
                    if '/' in address:
                        address, _ = address.split('/', 1)
                    ips.append(netaddr.IPAddress(address))
            except IndexError:
                pass
    return ips


def execute_ifconfig(*ifconfig_args, **execute_params):
    command = ('/sbin/ifconfig',) + ifconfig_args
    result = sh.execute(command, stdin=False, stdout=True, stderr=True,
                        expect_exit_status=None, **execute_params)
    if result.exit_status or not result.stdout:
        raise IfconfigError(error=result.stderr)
    return result.stdout
