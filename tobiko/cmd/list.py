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
import argparse
import logging
import sys

from tobiko.cmd import base

LOG = logging.getLogger(__name__)


class ListUtil(base.TobikoCMD):

    def __init__(self):
        super(ListUtil, self).__init__()
        self.parser = self.get_parser()
        self.args = (self.parser).parse_args()

    def get_parser(self):
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('--stacks', '-s',
                            help="List stacks (created by Tobiko)",
                            const='list_stacks',
                            action='store_const', dest='action')
        parser.add_argument('--templates', '-t',
                            help="List templates provided by Tobiko",
                            const='list_templates',
                            action='store_const', dest='action')
        return parser

    def list_stacks(self):
        """Lists stacks created by Tobiko."""
        for stack in self.stackManager.get_stacks_match_templates():
            print(stack)

    def list_templates(self):
        """Lists stacks created by Tobiko."""
        for template in self.stackManager.get_templates_names():
            print(template)


def main():
    """List CLI main entry."""
    list_cmd = ListUtil()
    if list_cmd.args.action:
        action_func = getattr(list_cmd, list_cmd.args.action)
        action_func()
    else:
        list_cmd.list_templates()


if __name__ == '__main__':
    sys.exit(main())
