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

from tobiko.shell.sh import _command
from tobiko.shell.sh import _exception
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _local
from tobiko.shell.sh import _io
from tobiko.shell.sh import _process
from tobiko.shell.sh import _ssh


shell_command = _command.shell_command

ShellError = _exception.ShellError
ShellCommandFailed = _exception.ShellCommandFailed
ShellTimeoutExpired = _exception.ShellTimeoutExpired
ShellProcessTeriminated = _exception.ShellProcessTeriminated
ShellProcessNotTeriminated = _exception.ShellProcessNotTeriminated
ShellStdinClosed = _exception.ShellStdinClosed

execute = _execute.execute
execute_process = _execute.execute_process
ShellExecuteResult = _execute.ShellExecuteResult

join_chunks = _io.join_chunks

local_execute = _local.local_execute
local_process = _local.local_process
LocalShellProcessFixture = _local.LocalShellProcessFixture
LocalExecutePathFixture = _local.LocalExecutePathFixture

process = _process.process
ShellProcessFixture = _process.ShellProcessFixture

ssh_process = _ssh.ssh_process
ssh_execute = _ssh.ssh_execute
SSHShellProcessFixture = _ssh.SSHShellProcessFixture
