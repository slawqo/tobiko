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

from tobiko.shell.ssh import _config
from tobiko.shell.ssh import _client
from tobiko.shell.ssh import _command
from tobiko.shell.ssh import _forward
from tobiko.shell.ssh import _skip


SSHHostConfig = _config.SSHHostConfig
ssh_host_config = _config.ssh_host_config

SSHClientFixture = _client.SSHClientFixture
ssh_client = _client.ssh_client
ssh_command = _command.ssh_command
ssh_proxy_client = _client.ssh_proxy_client
SSHConnectFailure = _client.SSHConnectFailure
gather_ssh_connect_parameters = _client.gather_ssh_connect_parameters
SSHClientType = _client.SSHClientType
ssh_client_fixture = _client.ssh_client_fixture


reset_default_ssh_port_forward_manager = \
    _forward.reset_default_ssh_port_forward_manager
get_port_forward_url = _forward.get_forward_url
get_forward_port_address = _forward.get_forward_port_address
SSHTunnelForwarderFixture = _forward.SSHTunnelForwarderFixture
SSHTunnelForwarder = _forward.SSHTunnelForwarder

has_ssh_proxy_jump = _skip.has_ssh_proxy_jump
skip_unless_has_ssh_proxy_jump = _skip.skip_unless_has_ssh_proxy_jump
