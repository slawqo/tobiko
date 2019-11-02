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

import collections
import os
import sys
import typing  # noqa

from heatclient.common import template_utils
import yaml

import tobiko


TEMPLATE_SUFFIX = '.yaml'

TEMPLATE_DIRS = list(sys.path)


class HeatTemplateFixture(tobiko.SharedFixture):

    template = None  # type: typing.Dict[str, typing.Any]
    template_files = None
    template_yaml = None

    def __init__(self, template=None, template_files=None):
        super(HeatTemplateFixture, self).__init__()
        if template:
            self.template = template
        if template_files:
            self.template_files = template_files

    def setup_fixture(self):
        self.setup_template()

    def setup_template(self):
        self.template_yaml = yaml.safe_dump(self.template)

    @property
    def outputs(self):
        template = self.template
        return template and template.get('outputs') or None

    @property
    def parameters(self):
        template = self.template
        return template and template.get('parameters') or None

    @property
    def resources(self):
        template = self.template
        return template and template.get('resources') or None


class HeatTemplateFileFixture(HeatTemplateFixture):

    template_file = None
    template_dirs = None
    template_files = None

    def __init__(self, template_file=None, template_dirs=None):
        super(HeatTemplateFileFixture, self).__init__()
        if template_file:
            self.template_file = template_file
        if template_dirs:
            self.template_dirs = template_dirs

    def setup_template(self):
        if self.template_dirs or not os.path.isfile(self.template_file):
            template_dirs = self.template_dirs or TEMPLATE_DIRS
            template_file = find_heat_template_file(
                template_file=self.template_file,
                template_dirs=template_dirs)
        template_files, template = template_utils.get_template_contents(
            template_file=template_file)
        self.template = template
        self.template_files = template_files
        super(HeatTemplateFileFixture, self).setup_template()


def heat_template(obj, template_files=None):
    if isinstance(obj, collections.Mapping):
        template = HeatTemplateFixture(template=obj,
                                       template_files=template_files)
    else:
        template = tobiko.get_fixture(obj)

    if not isinstance(template, HeatTemplateFixture):
        msg = "Object {!r} is not an HeatTemplateFixture".format(template)
        raise TypeError(msg)
    return template


def heat_template_file(template_file, template_dirs=None):
    return HeatTemplateFileFixture(template_file=template_file,
                                   template_dirs=template_dirs)


def find_heat_template_file(template_file, template_dirs):
    for template_dir in template_dirs:
        template_path = os.path.join(template_dir, template_file)
        if os.path.exists(template_path):
            return template_path

    msg = "Template file {!r} not found in directories {!r}".format(
        template_file, template_dirs)
    raise IOError(msg)
