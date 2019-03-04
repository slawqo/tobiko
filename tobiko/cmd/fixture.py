# Copyright 2018 Red Hat
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

import argparse
import sys

from oslo_log import log

import tobiko
from tobiko.cmd import base

LOG = log.getLogger(__name__)


class FixtureUtil(base.TobikoCMD):

    def __init__(self):
        super(FixtureUtil, self).__init__()
        self.parser = self.get_parser()
        self.args = self.parser.parse_args()

    def get_parser(self):
        parser = argparse.ArgumentParser(add_help=True)

        subparsers_params = {}
        subparsers = parser.add_subparsers(**subparsers_params)
        for subcommand_name in ['cleanup', 'list', 'setup']:
            subcommand_parser = subparsers.add_parser(
                subcommand_name, help=(subcommand_name + ' fixtures'))
            subcommand_parser.set_defaults(subcommand=subcommand_name)
            subcommand_parser.add_argument(
                '--config', '-c',
                default='.stestr.conf',
                help=("Set a stestr config file to use with this command. "
                      "If one isn't specified then .stestr.conf in the "
                      "directory that a command is running from is used"))
            subcommand_parser.add_argument(
                '--repo-type', '-r',
                choices=['file'],
                default='file',
                help=("Select the repo backend to use"))
            subcommand_parser.add_argument(
                '--repo-url', '-u',
                default=None,
                help=("Set the repo url to use. An acceptable value for "
                      "this depends on the repository type used."))

        return parser

    def execute(self):
        action = self.args.subcommand or 'list'
        if action == 'list':
            return self.list_fixtures()
        elif action == 'setup':
            return self.setup_fixtures()
        elif action == 'cleanup':
            return self.cleanup_fixtures()

    def discovertest_cases(self):
        return tobiko.discover_testcases(config=self.args.config)

    def list_fixtures(self, stream=sys.stdout):
        stream = stream or sys.stdout
        test_cases = tobiko.discover_testcases()
        fixtures_names = tobiko.list_required_fixtures(test_cases)
        stream.write('\n'.join(fixtures_names) + '\n')

    def setup_fixtures(self):
        test_cases = tobiko.discover_testcases()
        for fixture in tobiko.setup_required_fixtures(test_cases):
            fixture_name = tobiko.get_fixture_name(fixture)
            LOG.debug("Fixture setUp called, %s", fixture_name)

    def cleanup_fixtures(self):
        test_cases = tobiko.discover_testcases()
        for fixture in tobiko.cleanup_required_fixtures(test_cases):
            fixture_name = tobiko.get_fixture_name(fixture)
            LOG.debug("Fixture cleanUp called, %s", fixture_name)


def main():
    """Create CLI main entry."""
    fixture_util = FixtureUtil()
    fixture_util.execute()


if __name__ == '__main__':
    sys.exit(main())
