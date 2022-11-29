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

import io
import sys
import typing
import unittest

import tobiko


def get_test_result() -> unittest.TestResult:
    return tobiko.setup_fixture(TestResultFixture).result


class TestResultFixture(tobiko.SharedFixture):

    verbosity = 2
    stream = sys.stderr
    description = True
    result: unittest.TestResult

    def setup_fixture(self):
        self.result = TestResult(stream=self.stream,
                                 verbosity=self.verbosity,
                                 description=self.description)


class TestResult(unittest.TextTestResult):

    def __init__(self,
                 stream: typing.TextIO,
                 description: bool,
                 verbosity: int):
        super().__init__(stream=TextIOWrapper(stream),
                         descriptions=description,
                         verbosity=verbosity)
        self.buffer = True

    def startTest(self, test: unittest.TestCase):
        tobiko.push_test_case(test)
        super().startTest(test)

    def stopTest(self, test: unittest.TestCase) -> None:
        super().stopTestRun()
        actual_test = tobiko.pop_test_case()
        assert actual_test == test
        tobiko.remove_test_from_all_shared_resources(test.id())


class TextIOWrapper(io.TextIOWrapper):

    def __init__(self, stream: typing.TextIO):
        super().__init__(buffer=stream.buffer,
                         encoding='UTF-8',
                         errors='strict',
                         line_buffering=True,
                         write_through=False)

    def writeln(self, line: str):
        self.write(line + '\n')
