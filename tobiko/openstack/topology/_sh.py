# Copyright 2021 Red Hat
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

import typing

import tobiko
from tobiko.openstack.topology import _topology
from tobiko.shell import sh


def list_nodes_processes(command: str = None,
                         command_line: sh.ShellCommandType = None,
                         hostnames: typing.Iterable[str] = None,
                         topology: _topology.OpenStackTopology = None,
                         **list_processes_params) \
        -> tobiko.Selection[sh.PsProcess]:
    processes = tobiko.Selection[sh.PsProcess]()
    nodes = _topology.list_openstack_nodes(topology=topology,
                                           hostnames=hostnames)
    for node in nodes:
        processes += sh.list_processes(command=command,
                                       command_line=command_line,
                                       ssh_client=node.ssh_client,
                                       **list_processes_params)
    return processes
