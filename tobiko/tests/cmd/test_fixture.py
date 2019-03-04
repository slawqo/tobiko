# Copyright (c) 2018 Red Hat
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

import fixtures

from tobiko.cmd import fixture
from tobiko.tests import unit


class ExitCalled(Exception):
    pass


class MyFixture1(fixtures.Fixture):
    pass


class MyFixture2(fixtures.Fixture):
    pass


class FixtureUtilTest(unit.TobikoUnitTest):

    command_name = 'tobiko-fixture'
    command_class = fixture.FixtureUtil

    def setUp(self):
        super(FixtureUtilTest, self).setUp()
        self.mock_error = self.patch('argparse.ArgumentParser.error',
                                     side_effect=self.fail)

    def patch_argv(self, argv=None, subcommand=None):
        subcommand = subcommand or 'list'
        argv = [self.command_name, subcommand] + list(argv or [])
        return self.patch('sys.argv', argv)

    def test_init(self, argv=None, subcommand=None,
                  config_file='.stestr.conf', repo_type='file',
                  repo_url=None):
        self.patch_argv(argv=argv, subcommand=subcommand)
        cmd = self.command_class()
        self.mock_error.assert_not_called()
        self.assertIsNotNone(cmd.args)
        self.assertEqual(config_file, cmd.args.config)
        self.assertEqual(subcommand or 'list', cmd.args.subcommand)
        self.assertEqual(repo_type, cmd.args.repo_type)
        self.assertEqual(repo_url, cmd.args.repo_url)

    def test_init_with_c(self):
        self.test_init(argv=['-c', 'some-config-file'],
                       config_file='some-config-file')

    def test_init_with_config(self):
        self.test_init(argv=['--config', 'some-config-file'],
                       config_file='some-config-file')

    def test_init_with_r(self):
        self.test_init(argv=['-r', 'file'], repo_type='file')

    def test_init_with_repo_type_file(self):
        self.test_init(argv=['--repo-type', 'file'], repo_type='file')

    def test_init_with_repo_type_sql(self):
        self.assertRaises(self.failureException, self.test_init,
                          argv=['--repo-type', 'sql'])

    def test_init_with_u(self):
        self.test_init(argv=['-u', 'some-url'], repo_url='some-url')

    def test_init_with_repo_url(self):
        self.test_init(argv=['--repo-url', 'some-url'], repo_url='some-url')

    def test_init_with_list(self):
        self.test_init(subcommand='list')

    def test_init_with_seutp(self):
        self.test_init(subcommand='setup')

    def test_init_with_cleanup(self):
        self.test_init(subcommand='cleanup')
