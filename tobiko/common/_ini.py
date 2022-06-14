# Copyright 2022 Red Hat
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

IniFileTextType = typing.Union[str, typing.Iterable[str]]


def parse_ini_file(text: IniFileTextType,
                   section='DEFAULT') \
        -> typing.Dict[typing.Tuple[str, str], typing.Any]:
    if isinstance(text, str):
        text = text.splitlines()
    content: typing.Dict[typing.Tuple[str, str], typing.Any] = {}
    for line in text:
        line = line.rsplit('#', 1)[0]  # Remove comments
        line = line.strip()  # strip whitespaces
        if not line:
            # skip empty line
            continue
        if line.startswith('['):
            # parse section name
            section = line[1:-1].strip()
            continue
        if '=' in line:
            left, right = line.split('=', 1)
            content[section, left.strip()] = right.strip()
    return content
