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


from tobiko.shell import sh
from tobiko.tests import unit


class JoinChunksTest(unit.TobikoUnitTest):

    def test_join_chunks(self, chunks=None, expected_result=None):
        chunks = chunks or []
        actual_result = sh.join_chunks(chunks)
        self.assertIsInstance(actual_result, type(expected_result))
        if len(chunks) > 1:
            self.assertEqual(expected_result, actual_result)
        else:
            self.assertIs(expected_result, actual_result)

    def test_join_chunks_with_bytes(self):
        self.test_join_chunks([b'a', b'b', b'c'], b'abc')

    def test_join_chunks_with_one_bytes(self):
        self.test_join_chunks([b'abc'], b'abc')

    def test_join_chunks_with_bytes_and_nones(self):
        self.test_join_chunks([None, b'ab', None, b'cd'], b'abcd')

    def test_join_chunks_with_strings(self):
        self.test_join_chunks(['a', 'b', 'c'], 'abc')

    def test_join_chunks_with_one_string(self):
        self.test_join_chunks(['abc'], 'abc')

    def test_join_chunks_with_strings_and_nones(self):
        self.test_join_chunks([None, 'ab', None, 'cd'], 'abcd')

    def test_join_chunks_with_unicodes(self):
        self.test_join_chunks([u'a', u'b', u'c'], u'abc')

    def test_join_chunks_with_one_unicode(self):
        self.test_join_chunks([u'abc'], u'abc')

    def test_join_chunks_with_unicodes_and_nones(self):
        self.test_join_chunks([None, u'ab', None, u'cd'], u'abcd')
