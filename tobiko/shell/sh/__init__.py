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

from tobiko.shell.sh import _cmdline
from tobiko.shell.sh import _command
from tobiko.shell.sh import _exception
from tobiko.shell.sh import _execute
from tobiko.shell.sh import _hostname
from tobiko.shell.sh import _io
from tobiko.shell.sh import _local
from tobiko.shell.sh import _mktemp
from tobiko.shell.sh import _nameservers
from tobiko.shell.sh import _process
from tobiko.shell.sh import _ps
from tobiko.shell.sh import _reboot
from tobiko.shell.sh import _sftp
from tobiko.shell.sh import _ssh
from tobiko.shell.sh import _uptime
from tobiko.shell.sh import _wc


get_command_line = _cmdline.get_command_line

ShellCommand = _command.ShellCommand
ShellCommandType = _command.ShellCommandType
shell_command = _command.shell_command

ShellError = _exception.ShellError
ShellCommandFailed = _exception.ShellCommandFailed
ShellTimeoutExpired = _exception.ShellTimeoutExpired
ShellProcessTerminated = _exception.ShellProcessTerminated
ShellProcessNotTerminated = _exception.ShellProcessNotTerminated
ShellStdinClosed = _exception.ShellStdinClosed

execute = _execute.execute
execute_process = _execute.execute_process
execute_result = _execute.execute_result
ShellExecuteResult = _execute.ShellExecuteResult

HostNameError = _hostname.HostnameError
get_hostname = _hostname.get_hostname
ssh_hostname = _hostname.ssh_hostname

join_chunks = _io.join_chunks
ShellStdout = _io.ShellStdout
select_files = _io.select_files

local_execute = _local.local_execute
local_process = _local.local_process
LocalShellProcessFixture = _local.LocalShellProcessFixture
LocalExecutePathFixture = _local.LocalExecutePathFixture

make_temp_dir = _mktemp.make_temp_dir

ListNameserversFixture = _nameservers.ListNameserversFixture
list_nameservers = _nameservers.list_nameservers

process = _process.process
str_from_stream = _process.str_from_stream
ShellProcessFixture = _process.ShellProcessFixture

PsError = _ps.PsError
PsProcess = _ps.PsProcess
PsWaitTimeout = _ps.PsWaitTimeout
list_all_processes = _ps.list_all_processes
list_kernel_processes = _ps.list_kernel_processes
list_processes = _ps.list_processes
wait_for_processes = _ps.wait_for_processes

reboot_host = _reboot.reboot_host
RebootHostError = _reboot.RebootHostError
RebootHostOperation = _reboot.RebootHostOperation
RebootHostTimeoutError = _reboot.RebootHostTimeoutError
RebootHostMethod = _reboot.RebootHostMethod
crash_method = RebootHostMethod.CRASH
hard_reset_method = RebootHostMethod.HARD
soft_reset_method = RebootHostMethod.SOFT

put_file = _sftp.put_file
get_file = _sftp.get_file

ssh_process = _ssh.ssh_process
ssh_execute = _ssh.ssh_execute
SSHShellProcessFixture = _ssh.SSHShellProcessFixture

get_uptime = _uptime.get_uptime

assert_file_size = _wc.assert_file_size
get_file_size = _wc.get_file_size
