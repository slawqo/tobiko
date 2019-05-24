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

import shutil
import tempfile

import mock

from tobiko.tests import base
from tobiko.common import _fixture


class TobikoUnitTest(base.TobikoTest):

    def setUp(self):
        super(TobikoUnitTest, self).setUp()
        # Protect from mis-configuring logging
        self.patch('oslo_log.log.setup')
        self.fixture_manager = manager = _fixture.FixtureManager()
        self.patch_object(_fixture, 'FIXTURES', manager)

    def patch(self, target, *args, **kwargs):
        context = mock.patch(target, *args, **kwargs)
        mock_object = context.start()
        self.addCleanup(context.stop)
        return mock_object

    def patch_object(self, target, attribute, *args, **kwargs):
        context = mock.patch.object(target, attribute, *args, **kwargs)
        mock_object = context.start()
        self.addCleanup(context.stop)
        return mock_object

    def create_tempdir(self, *args, **kwargs):
        dir_path = tempfile.mkdtemp(*args, **kwargs)
        self.addCleanup(shutil.rmtree(dir_path, ignore_errors=True))
        return dir_path
