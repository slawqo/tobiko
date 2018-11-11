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
import urllib2

from tobiko.cmd import base
from tobiko.common import constants
from tobiko.common import exceptions as exc

LOG = logging.getLogger(__name__)


class CreateUtil(base.TobikoCMD):

    def __init__(self):
        super(CreateUtil, self).__init__()
        self.parser = self.get_parser()
        self.args = (self.parser).parse_args()

    def get_parser(self):
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument(
            '--stack', '-s',
            help="The name of the stack to create.\n"
                 "This is based on the template name in templates dir")
        parser.add_argument(
            '--all', '-a', action='store_true', dest='all',
            help="Create all the stacks defined in Tobiko.")
        return parser

    def create_stack(self, stack_name=None, all_stacks=False):
        """Creates a stack based on given arguments."""
        if all_stacks:
            templates = self.stackManager.get_templates_names()
            for template in templates:
                stack_name = template.split(constants.TEMPLATE_SUFFIX)[0]
                self.stackManager.create_stack(
                    stack_name, template, parameters=constants.DEFAULT_PARAMS)
                LOG.info("Created stack: %s" % stack_name)
        else:
            try:
                self.stackManager.create_stack(
                    stack_name, ''.join([stack_name,
                                         constants.TEMPLATE_SUFFIX]),
                    parameters=constants.DEFAULT_PARAMS)
                LOG.info("Created stack: %s" % stack_name)
            except urllib2.URLError:
                stacks = self.stackManager.get_templates_names(
                    strip_suffix=True)
                raise exc.MissingTemplateException(templates="\n".join(stacks))


def main():
    """Create CLI main entry."""
    create_cmd = CreateUtil()
    create_cmd.create_stack(create_cmd.args.stack,
                            create_cmd.args.all)


if __name__ == '__main__':
    sys.exit(main())
