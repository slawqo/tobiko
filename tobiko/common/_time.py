# Copyright 2020 Red Hat
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

import time as _time
import typing

from tobiko.common import _exception


Seconds = typing.Optional[float]


class SecondsValueError(_exception.TobikoException):
    message = "Invalid seconds value: {seconds}"


ToSecondsValue = typing.Union[float, int, str, bytearray, None]


def to_seconds(value: ToSecondsValue) -> Seconds:
    if value is None:
        return None
    else:
        return to_seconds_float(value)


def to_seconds_float(value: ToSecondsValue) -> float:
    return value and max(0., float(value)) or 0.


def time() -> float:
    return _time.time()


def sleep(seconds: Seconds):
    _time.sleep(to_seconds_float(seconds))


def true_seconds(*seconds: Seconds) -> typing.List[float]:
    result = []
    for value in seconds:
        value = to_seconds(value)
        if value is not None:
            result.append(value)
    return result


def min_seconds(*seconds: Seconds) -> Seconds:
    values = true_seconds(*seconds)
    if values:
        return min(values)
    else:
        return None


def max_seconds(*seconds: Seconds) -> Seconds:
    values = true_seconds(*seconds)
    if values:
        return max(values)
    else:
        return None
