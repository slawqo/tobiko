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

import io
import os
import tempfile

import tobiko
from tobiko.tests import unit


class ParseIniFileTest(unit.TobikoUnitTest):

    def test_parse_ini_file(self):
        text = """
        my_option = my value
        """
        result = tobiko.parse_ini_file(text=text)
        self.assertEqual({('DEFAULT', 'my_option'): 'my value'},
                         result)

    def test_parse_ini_with_lines(self):
        lines = ['a = 3',
                 'b=4']
        result = tobiko.parse_ini_file(text=lines)
        self.assertEqual({('DEFAULT', 'a'): '3',
                          ('DEFAULT', 'b'): '4'},
                         result)

    def test_parse_ini_with_io(self):
        text = """
        my_option = my value
        """
        fd, temp_file = tempfile.mkstemp(text=True)
        self.addCleanup(os.remove, temp_file)
        with os.fdopen(fd, 'wt') as stream:
            stream.write(text)

        with io.open(temp_file, 'rt') as stream:
            result = tobiko.parse_ini_file(text=stream)
        self.assertEqual({('DEFAULT', 'my_option'): 'my value'},
                         result)

    def test_parse_ini_file_with_default_section(self):
        text = """
        my_option = my value
        """
        result = tobiko.parse_ini_file(text=text, section='default-section')
        self.assertEqual({('default-section', 'my_option'): 'my value'},
                         result)

    def test_parse_ini_file_with_section(self):
        text = """
        [my_section]
        my_option = my value
        """
        result = tobiko.parse_ini_file(text=text)
        self.assertEqual({('my_section', 'my_option'): 'my value'}, result)

    def test_parse_ini_file_empty(self):
        result = tobiko.parse_ini_file(text='')
        self.assertEqual({}, result)

    def test_parse_ini_file_with_commented_option(self):
        text = """
        my_option = 1
        # my_option = 2
        """
        result = tobiko.parse_ini_file(text=text)
        self.assertEqual({('DEFAULT', 'my_option'): '1'},
                         result)

    def test_parse_ini_file_with_duplicate_option(self):
        text = """
        my_option = a
        my_option = b
        """
        result = tobiko.parse_ini_file(text=text)
        self.assertEqual({('DEFAULT', 'my_option'): 'b'},
                         result)
