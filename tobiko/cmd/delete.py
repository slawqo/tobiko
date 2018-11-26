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


class DeleteUtil(base.TobikoCMD):

    def __init__(self):
        super(DeleteUtil, self).__init__()
        self.parser = self.get_parser()
        self.args = (self.parser).parse_args()

    def get_parser(self):
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument(
            '--stack', '-s',
            help="The name of the stack to remove.")
        parser.add_argument(
            '--all', '-a', action='store_true', dest='all',
            help="Remove all the stacks created by Tobiko.")
        return parser

    def delete_stack(self, stack_name=None, all_stacks=False):
        """Deletes a stack based on given arguments."""
        if all_stacks or stack_name is None:
            stacks = self.stackManager.get_stacks_match_templates()
            for stack in stacks:
                self.stackManager.delete_stack(stack)
                LOG.info("Deleted stack: %s" % stack)
        else:
            self.stackManager.delete_stack(stack_name)
            LOG.info("Deleted stack: %s" % stack_name)


def main():
    """Delete CLI main entry."""
    delete_cmd = DeleteUtil()
    delete_cmd.delete_stack(delete_cmd.args.stack,
                            delete_cmd.args.all)


if __name__ == '__main__':
    sys.exit(main())
