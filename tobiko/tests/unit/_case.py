# Copyright 2019 Red Hat
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

import inspect
import shutil
import os
import tempfile

from oslo_log import log
import testtools

import tobiko
from tobiko.tests.unit import _patch


class PatchEnvironFixture(tobiko.SharedFixture):

    original_environ = None
    patch_environ = None
    new_environ = None

    def __init__(self, **patch_environ):
        super(PatchEnvironFixture, self).__init__()
        self.patch_environ = patch_environ

    def setup_fixture(self):
        self.original_environ = os.environ
        self.new_environ = dict(os.environ, **self.patch_environ)
        os.environ = self.new_environ

    def cleanup_fixture(self):
        os.environ = self.original_environ


class FixtureManagerPatch(tobiko.FixtureManager, _patch.PatchFixture):

    def init_fixture(self, obj, name):
        fixture = super(FixtureManagerPatch, self).init_fixture(
            obj=obj, name=name)
        self.addCleanup(tobiko.cleanup_fixture, fixture)
        return fixture

    def setup_fixture(self):
        self.patch(inspect.getmodule(tobiko.FixtureManager), 'FIXTURES',
                   self)


class TobikoUnitTest(_patch.PatchMixin, testtools.TestCase):

    patch_environ = {
        'http_proxy': 'http://127.0.0.1:88888',
        'https_proxy': 'http://127.0.0.1:88888',
        'no_proxy': '127.0.0.1'
    }

    def setUp(self):
        super(TobikoUnitTest, self).setUp()
        # Protect from mis-configuring logging
        self.patch(log, 'setup')

        # Make sure each unit test uses it's own fixture manager
        self.fixture_manager = manager = FixtureManagerPatch()
        self.useFixture(manager)
        self.useFixture(PatchEnvironFixture(**self.patch_environ))

    def create_tempdir(self, *args, **kwargs):
        dir_path = tempfile.mkdtemp(*args, **kwargs)
        self.addCleanup(shutil.rmtree(dir_path, ignore_errors=True))
        return dir_path
