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

import shlex
import typing  # noqa


class ShellCommand(tuple):

    def __repr__(self):
        return "ShellCommand([{!s}])".format(', '.join(self))

    def __str__(self):
        return list_to_command_line(self)

    def __add__(self, other):
        other = shell_command(other)
        return shell_command(tuple(self) + other)


ShellCommandType = typing.Union[ShellCommand, str, typing.Iterable]


def shell_command(command: ShellCommandType) -> ShellCommand:
    if isinstance(command, ShellCommand):
        return command
    elif isinstance(command, str):
        return ShellCommand(shlex.split(command))
    else:
        return ShellCommand(str(a) for a in command)


def list_to_command_line(seq):
    result = []
    for arg in seq:
        bs_buf = []

        # Add a space to separate this argument from the others
        if result:
            result.append(' ')

        needquote = (" " in arg) or ("\t" in arg) or not arg
        if needquote:
            result.append("'")

        for c in arg:
            if c == '\\':
                # Don't know if we need to double yet.
                bs_buf.append(c)
            elif c == '"':
                # Double backslashes.
                result.append('\\' * len(bs_buf)*2)
                bs_buf = []
                result.append('\\"')
            else:
                # Normal char
                if bs_buf:
                    result.extend(bs_buf)
                    bs_buf = []
                result.append(c)

        # Add remaining backslashes, if any.
        if bs_buf:
            result.extend(bs_buf)

        if needquote:
            result.extend(bs_buf)
            result.append("'")

    return ''.join(result)
