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
from testtools import content

from tobiko.common import _detail
from tobiko.common import _fixture


LOG = log.getLogger(__name__)


class CaptureLogFixture(_fixture.SharedFixture):

    level = None
    logger = logging.root
    handler = None
    format = "%(asctime)-15s %(levelname)s %(name)s | %(message)s"

    def __init__(self, test_case_id, logger=None, level=None, fmt=None):
        super(CaptureLogFixture, self).__init__()
        self.test_case_id = test_case_id
        if logger:
            self.logger = logger
        if level:
            self.level = level
        if fmt:
            self.format = fmt

    def setup_fixture(self):
        self.handler = handler = CaptureLogHandler(level=self.level)
        formatter = logging.Formatter(self.format)
        handler.setFormatter(formatter)
        self.addCleanup(self.logger.removeHandler, handler)
        self.logger.addHandler(handler)
        LOG.debug('--- BEGIN %s ---', self.test_case_id)
        self.addCleanup(LOG.debug, '--- END %s ---', self.test_case_id)

    def getDetails(self):
        handler = self.handler
        if handler:
            content_object = _detail.details_content(
                content_type=content.UTF8_TEXT,
                content_id=self.fixture_name,
                get_text=handler.format_all)
            return {'log': content_object}
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

    def format_all(self):
        for record in self.records:
            yield self.format(record) + '\n'
