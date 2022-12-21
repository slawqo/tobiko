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

import re
import typing

from packaging import version as _version

from tobiko import _exception


VERSION_PATTERN = re.compile(r"[0-9]*\.[0-9]*\.[0-9]*")


class InvalidVersion(_exception.TobikoException):
    message = "invalid version: {text}"


class VersionMismatch(_exception.TobikoException):
    message = "version mismatch {version} {cause}"
    cause = ''


try:
    VERSION_CLASSES = _version.LegacyVersion, _version.Version
except AttributeError:
    VERSION_CLASSES = _version.Version

Version = typing.Union[_version.Version]
VersionType = typing.Union[Version, str]


def get_version(obj: VersionType):
    if isinstance(obj, VERSION_CLASSES):
        return obj
    elif isinstance(obj, str):
        return parse_version(obj)
    else:
        raise TypeError(f'Cannot get version from object {obj!r}')


def parse_version(text: str) -> VersionType:
    match = VERSION_PATTERN.search(text.strip())
    if match is not None:
        text = match.group()
    try:
        return _version.Version(text)
    except _version.InvalidVersion as ex:
        raise InvalidVersion(text=text) from ex


def match_version(actual: VersionType,
                  min_version: VersionType = None,
                  max_version: VersionType = None) -> bool:
    try:
        check_version(actual=actual,
                      min_version=min_version,
                      max_version=max_version)
    except VersionMismatch:
        return False
    else:
        return True


def check_version(actual: VersionType,
                  min_version: VersionType = None,
                  max_version: VersionType = None,
                  mismatch_error=VersionMismatch):
    actual = get_version(actual)
    if min_version is not None:
        min_version = get_version(min_version)
        if actual < min_version:
            raise mismatch_error(
                version=actual,
                cause=f">= {max_version}")

    if max_version is not None:
        max_version = get_version(max_version)
        if actual >= max_version:
            raise mismatch_error(
                version=actual,
                cause=f">= {max_version}")
    return True
