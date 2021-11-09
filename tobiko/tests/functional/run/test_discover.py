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

import os
import typing

import testtools

from tobiko import run


class DiscoverTestIdsTest(testtools.TestCase):

    def test_discover_test_ids(self,
                               test_files: typing.List[str] = None):
        if test_files is None:
            test_files = [__file__]
        test_ids = run.discover_test_ids(test_files=test_files)
        self.assertIn(self.id(), test_ids)

    def test_forked_discover_test_ids(self,
                                      test_files: typing.List[str] = None):
        if test_files is None:
            test_files = [__file__]
        test_ids = run.forked_discover_test_ids(test_files=test_files)
        self.assertIn(self.id(), test_ids)

    def test_find_test_ids(self,
                           test_path: typing.List[str] = None,
                           forked=False):
        if test_path is None:
            test_path = [__file__]
        test_ids = run.find_test_ids(test_path=test_path, forked=forked)
        self.assertIn(self.id(), test_ids)

    def test_find_test_ids_with_test_dir(self):
        self.test_find_test_ids(test_path=[os.path.dirname(__file__)])

    def test_find_test_ids_with_forked(self):
        self.test_find_test_ids(forked=True)
