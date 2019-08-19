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

import logging

from oslo_log import log

import testtools
from testtools import content

from tobiko.common import _fixture


LOG = log.getLogger(__name__)


class CaptureLogFixture(_fixture.SharedFixture):

    level = None
    logger = logging.root
    handler = None

    def __init__(self, logger=None, level=None):
        super(CaptureLogFixture, self).__init__()
        if logger:
            self.logger = logger
        if level:
            self.level = level

    def setup_fixture(self):
        self.handler = handler = CaptureLogHandler(level=self.level)
        self.logger.addHandler(handler)
        self.addCleanup(self.logger.removeHandler, handler)

    def getDetails(self):
        if self.handler:
            return {'log': self.handler.content}
        else:
            return {}


class CaptureLogHandler(logging.Handler):

    def __init__(self, level=None):
        if level is None:
            from tobiko import config
            CONF = config.CONF
            if CONF.tobiko.debug:
                level = logging.DEBUG
            else:
                level = logging.INFO
        super(CaptureLogHandler, self).__init__(level)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    @property
    def content(self):
        return content.Content(content.UTF8_TEXT, self.format_all)

    def format_all(self):
        for record in self.records:
            yield (self.format(record) + '\n').encode()


class CaptureLogTest(testtools.TestCase):

    capture_log_level = logging.DEBUG
    capture_log_logger = logging.root

    def setUp(self):
        self.useFixture(CaptureLogFixture(level=self.capture_log_level,
                                          logger=self.capture_log_logger))
        super(CaptureLogTest, self).setUp()
