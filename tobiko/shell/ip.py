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


class IpError(tobiko.TobikoException):
    message = ("Unable to get IP addresses from host "
               "(exit_status={exit_status!r}): {error!s}")


INETS = {
    4: ['inet'],
    6: ['inet6'],
    None: ['inet', 'inet6']
}


def list_ip_addresses(ip_version=None, scope=None, **execute_params):
    inets = INETS.get(ip_version)
    if inets is None:
        error = "invalid IP version: {!r}".format(ip_version)
        raise IpError(error=error)

    output = execute_ip(['-o', 'address', 'list'], **execute_params)

    ips = tobiko.Selection()
    if output:
        for line in output.splitlines():
            fields = line.strip().split()
            inet = fields[2]
            if inet not in inets:
                continue  # List only address of selected IP version

            if scope:
                try:
                    scope_index = fields.index('scope')
                    if fields[scope_index + 1] != scope:
                        continue
                except (IndexError, ValueError):
                    continue

            address = fields[3]
            if '/' in address:
                # Remove netmask prefix length
                address, _ = address.split('/', 1)
            ips.append(netaddr.IPAddress(address))
    return ips


def list_network_namespaces(**execute_params):
    output = execute_ip(['-o', 'netns', 'list'], **execute_params)
    namespaces = tobiko.Selection()
    if output:
        for line in output.splitlines():
            fields = line.strip().split()
            namespace = fields[0]
            namespaces.append(namespace)
    return namespaces


def execute_ip(ifconfig_args, **execute_params):
    command = ['/sbin/ip'] + ifconfig_args
    result = sh.execute(command, stdin=False, stdout=True, stderr=True,
                        expect_exit_status=None, **execute_params)
    if result.exit_status:
        raise IpError(error=result.stderr, exit_status=result.exit_status)
    return result.stdout
