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
import typing

from heatclient.common import template_utils
import yaml

import tobiko


TEMPLATE_SUFFIX = '.yaml'

TEMPLATE_DIRS = list(sys.path)


class HeatTemplateFixture(tobiko.SharedFixture):

    template_yaml: str

    def __init__(self,
                 template: typing.Mapping[str, typing.Any] = None,
                 template_files: typing.Mapping = None):
        super(HeatTemplateFixture, self).__init__()
        self.template: typing.Dict[str, typing.Any] = {}
        if template is not None:
            self.template.update(template)
        self.template_files: typing.Dict[str, typing.Any] = {}
        if template_files is not None:
            self.template_files.update(template_files)

    def setup_fixture(self):
        self.setup_template()

    def setup_template(self):
        # Ensure main sections are dictionaries
        tobiko.check_valid_type(self.outputs, collections.Mapping)
        tobiko.check_valid_type(self.parameters, collections.Mapping)
        tobiko.check_valid_type(self.resources, collections.Mapping)
        self.template_yaml = yaml.safe_dump(self.template)

    @property
    def outputs(self) -> typing.Dict[str, typing.Any]:
        return dict(self.template.get('outputs', {}))

    @property
    def parameters(self) -> typing.Dict[str, typing.Any]:
        return dict(self.template.get('parameters', {}))

    @property
    def resources(self) -> typing.Dict[str, typing.Any]:
        return dict(self.template.get('resources', {}))


class HeatTemplateFileFixture(HeatTemplateFixture):

    def __init__(self,
                 template_file: str,
                 template_dirs: typing.Iterable[str] = None):
        super(HeatTemplateFileFixture, self).__init__()
        self.template_file = template_file
        if template_dirs is None:
            template_dirs = TEMPLATE_DIRS
        self.template_dirs: typing.List[str] = list(template_dirs)

    def setup_template(self):
        template_file = self.template_file
        if self.template_dirs or not os.path.isfile(template_file):
            template_dirs = self.template_dirs or TEMPLATE_DIRS
            template_file = find_heat_template_file(
                template_file=self.template_file,
                template_dirs=template_dirs)
        template_files, template = template_utils.get_template_contents(
            template_file=template_file)
        self.template = template
        self.template_files = template_files
        super(HeatTemplateFileFixture, self).setup_template()


HeatTemplateType = typing.Union[typing.Mapping[str, typing.Any],
                                HeatTemplateFixture]


def heat_template(obj: HeatTemplateType,
                  template_files: typing.Mapping = None) \
        -> HeatTemplateFixture:
    if isinstance(obj, collections.Mapping):
        template = HeatTemplateFixture(template=obj,
                                       template_files=template_files)
    else:
        template = tobiko.get_fixture(obj)

    tobiko.check_valid_type(template, HeatTemplateFixture)
    return template


def heat_template_file(template_file: str,
                       template_dirs: typing.Iterable[str] = None):
    return HeatTemplateFileFixture(template_file=template_file,
                                   template_dirs=template_dirs)


def find_heat_template_file(template_file: str,
                            template_dirs: typing.Iterable[str]):
    for template_dir in template_dirs:
        template_path = os.path.join(template_dir, template_file)
        if os.path.exists(template_path):
            return template_path

    msg = "Template file {!r} not found in directories {!r}".format(
        template_file, template_dirs)
    raise IOError(msg)
