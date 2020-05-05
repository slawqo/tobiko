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
import subprocess


TOP_DIR = os.path.dirname(os.path.dirname(__file__))
if TOP_DIR not in sys.path:
    sys.path.insert(0, TOP_DIR)

from tools import common  # noqa

LOG = common.get_logger(__name__)


# Output dirs
TOX_REPORT_DIR = common.normalize_path(
    os.environ.get('TOX_REPORT_DIR', os.getcwd()))

TOX_REPORT_NAME = os.environ.get('TOX_REPORT_NAME', 'test_results')
TOX_REPORT_PREFIX = os.path.join(TOX_REPORT_DIR, TOX_REPORT_NAME)

TOX_REPORT_LOG = os.environ.get(
    'TOX_REPORT_LOG', TOX_REPORT_PREFIX + '.log')

TOX_REPORT_SUBUNIT = os.environ.get(
    'TOX_REPORT_SUBUNIT', TOX_REPORT_PREFIX + '.subunit')

TOX_REPORT_HTML = os.environ.get(
    'TOX_REPORT_HTML', TOX_REPORT_PREFIX + '.html')

TOX_REPORT_XML = os.environ.get(
    'TOX_REPORT_XML', TOX_REPORT_PREFIX + '.xml')


def main():
    common.setup_logging()
    try:
        succeeded = run_tests()
        if succeeded:
            LOG.info('SUCCEEDED')
        else:
            LOG.info('FAILED')
            sys.exit(1)

    except Exception:
        LOG.exception('ERROR')
        sys.exit(2)


def run_tests():
    cleanup_report_dir()
    log_environ()

    succeeded = True
    try:
        run_test_cases()
    except subprocess.CalledProcessError:
        succeeded = False

    try:
        log_tests_results()
    except subprocess.CalledProcessError:
        if succeeded:
            raise

    make_subunit_file()
    make_html_file()
    try:
        make_xml_file()
    except subprocess.CalledProcessError:
        if succeeded:
            raise

    return succeeded


def cleanup_report_dir():
    for report_file in [TOX_REPORT_LOG, TOX_REPORT_SUBUNIT, TOX_REPORT_HTML,
                        TOX_REPORT_XML]:
        if not common.make_dir(os.path.dirname(report_file)):
            common.remove_file(report_file)


def log_environ():
    common.execute('env | sort >> "{log_file}"', log_file=TOX_REPORT_LOG,
                   capture_stdout=False)


def log_tests_results():
    common.execute('stestr last --all-attachments >> "{log_file}"',
                   log_file=TOX_REPORT_LOG,
                   capture_stdout=False)


def run_test_cases():
    common.execute('stestr run --slowest {posargs}',
                   posargs=common.get_posargs(),
                   capture_stdout=False)


def make_subunit_file():
    common.execute('stestr last --subunit > "{subunit_file}"',
                   subunit_file=TOX_REPORT_SUBUNIT,
                   capture_stdout=False)


def make_html_file():
    common.execute('subunit2html "{subunit_file}" "{html_file}"',
                   subunit_file=TOX_REPORT_SUBUNIT,
                   html_file=TOX_REPORT_HTML,
                   capture_stdout=False)


def make_xml_file():
    common.execute('subunit2junitxml "{subunit_file}" -o "{xml_file}"',
                   subunit_file=TOX_REPORT_SUBUNIT,
                   xml_file=TOX_REPORT_XML,
                   capture_stdout=False)


if __name__ == '__main__':
    main()
