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

import contextlib
import os
import subprocess

import testtools
import yaml

from tobiko.openstack import keystone


class TobikoKeystoneCredentialsCommandTest(testtools.TestCase):

    def test_execute(self):
        with execute('tobiko-keystone-credentials') as process:
            actual = yaml.full_load(process.stdout)

        expected = keystone.default_keystone_credentials().to_dict()
        self.assertEqual(expected, actual)


@contextlib.contextmanager
def execute(command, check_exit_status=0):
    process = subprocess.Popen(command,
                               shell=True,
                               env=os.environ,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)

    try:
        yield process

        process.wait()
        if (check_exit_status is not None and
                check_exit_status != process.returncode):
            error = process.stderr.read()
            message = "Unexpected exit status ({!s}):\n{!s}".format(
                process.returncode, error)
            raise RuntimeError(message)

    finally:
        if process.returncode is None:
            process.kill()
