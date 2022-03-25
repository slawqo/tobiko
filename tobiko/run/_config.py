# Copyright (c) 2021 Red Hat, Inc.
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

import typing
import os

import tobiko


class RunConfigFixture(tobiko.SharedFixture):

    test_path: typing.List[str]
    test_filename: str = 'test_*.py'
    python_path: typing.Optional[typing.List[str]] = None
    workers_count: typing.Optional[int] = None

    def setup_fixture(self):
        package_file = os.path.realpath(os.path.realpath(tobiko.__file__))
        package_dir = os.path.dirname(package_file)
        tobiko_dir = os.path.dirname(package_dir)
        self.test_path = [os.path.join(tobiko_dir, 'tobiko', 'tests', 'unit')]

    @property
    def forked(self) -> bool:
        return self.workers_count is not None and self.workers_count != 1


def run_confing(obj=None) -> RunConfigFixture:
    if obj is None:
        return tobiko.setup_fixture(RunConfigFixture)
    fixture = tobiko.get_fixture(obj)
    tobiko.check_valid_type(fixture, RunConfigFixture)
    return tobiko.setup_fixture(fixture)
