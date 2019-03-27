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

import os
import sys

from oslo_log import log
from tobiko.cmd import base
from tobiko.common import constants
from tobiko.common import exceptions

LOG = log.getLogger(__name__)


class CreateUtil(base.TobikoCMD):

    def get_parser(self):
        parser = super(CreateUtil, self).get_parser()
        parser.add_argument(
            '--stack', '-s',
            help="The name of the stack to create.\n"
                 "This is based on the template name in templates dir")
        parser.add_argument(
            '--playbook', '-p',
            help="The name of the playbook to execute.\n"
                 "This is based on the playbook name in playbooks dir")
        parser.add_argument(
            '--all', '-a', action='store_true', dest='all',
            help="Create all the stacks defined in Tobiko.")
        parser.add_argument(
            '--wait', '-w', action='store_true', dest='wait',
            help="Wait for stack to reach CREATE_COMPLETE status before "
            "exiting.")
        return parser

    def create_stacks(self, stack_name=None, all_stacks=False, wait=False):
        """Creates a stack based on given arguments."""
        if all_stacks or stack_name is None:
            templates = self.stackManager.get_templates_names()
        else:
            templates = [stack_name + constants.TEMPLATE_SUFFIX]
        for template in templates:
            stack_name = os.path.splitext(template)[0]
            self.stackManager.create_stack(
                stack_name=stack_name,
                template_name=template,
                parameters=constants.DEFAULT_PARAMS,
                wait=wait)

    def run_playbook(self, playbook):
        """Executes given playbook."""
        self.ansibleManager.run_playbook(playbook, mode='create')


class NoSuchTemplateError(exceptions.TobikoException):
    message = "No such template. Existing templates:\n%(templates)s"


def main():
    """Create CLI main entry."""
    create_cmd = CreateUtil()
    create_cmd.set_stream_handler_logging_level()
    if create_cmd.args.playbook:
        create_cmd.run_playbook(create_cmd.args.playbook)
    else:
        create_cmd.create_stacks(stack_name=create_cmd.args.stack,
                                 all_stacks=create_cmd.args.all,
                                 wait=create_cmd.args.wait)


if __name__ == '__main__':
    sys.exit(main())
