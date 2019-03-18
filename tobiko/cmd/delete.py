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

import logging
import sys

from tobiko.cmd import base

LOG = logging.getLogger(__name__)


class DeleteUtil(base.TobikoCMD):

    def get_parser(self):
        parser = super(DeleteUtil, self).get_parser()
        parser.add_argument(
            '--stack', '-s',
            help="The name of the stack to remove.")
        parser.add_argument(
            '--all', '-a', action='store_true', dest='all',
            help="Remove all the stacks created by Tobiko.")
        parser.add_argument(
            '--wait', '-w', action='store_true', dest='wait',
            help="Wait for stack to be deleted before exiting.")
        parser.add_argument(
            '--playbook', '-p',
            help="The name of the playbook to execute in delete mode.")
        return parser

    def delete_stack(self, stack_name=None, all_stacks=False, wait=False):
        """Deletes a stack based on given arguments."""
        if all_stacks or stack_name is None:
            stacks = self.stackManager.get_stacks_match_templates()
            for stack in stacks:
                self.stackManager.delete_stack(stack, wait=wait)
                LOG.info("Deleted stack: %s", stack)
        else:
            self.stackManager.delete_stack(stack_name, wait=wait)
            LOG.info("Deleted stack: %s", stack_name)

    def run_playbook(self, playbook):
        """Executes given playbook."""
        self.ansibleManager.run_playbook(playbook, mode='delete')


def main():
    """Delete CLI main entry."""
    delete_cmd = DeleteUtil()
    delete_cmd.set_stream_handler_logging_level()
    if delete_cmd.args.playbook:
        delete_cmd.run_playbook(delete_cmd.args.playbook)
    else:
        delete_cmd.delete_stack(stack_name=delete_cmd.args.stack,
                                all_stacks=delete_cmd.args.all,
                                wait=delete_cmd.args.wait)


if __name__ == '__main__':
    sys.exit(main())
