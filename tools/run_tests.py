#!/usr/bin/env python3
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
import psutil
import signal
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

TOX_RUN_TESTS_TIMEOUT = float(os.environ.get('TOX_RUN_TESTS_TIMEOUT') or 0.)

TOX_PYDEV_DEBUG = bool(
    os.environ.get('TOX_PYDEV_DEBUG', 'false').lower() in
    ['true', 'yes', '1'])


def main():
    common.setup_logging()
    try:
        succeeded = run_tests()
        if succeeded:
            LOG.info('SUCCEEDED')
            sys.exit(0)
        else:
            LOG.info('FAILED')
            sys.exit(1)

    except Exception:
        LOG.exception('ERROR')
        sys.exit(2)


def run_tests():
    setup_timeout()
    cleanup_report_dir()
    log_environ()

    if TOX_PYDEV_DEBUG:
        debug_test_cases()
        return True

    succeeded = True
    try:
        run_test_cases()
    except (subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            ProcessLookupError) as ex:
        LOG.error(f"Error while running test cases.\n{ex}")
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


def setup_timeout():

    if TOX_RUN_TESTS_TIMEOUT > 0.:

        def handle_timeout(_signum, _frame):
            LOG.error(
                f"run_tests.py timeout out after {TOX_RUN_TESTS_TIMEOUT} "
                "seconds")
            terminate_childs()
            raise subprocess.TimeoutExpired("run_tests.py",
                                            TOX_RUN_TESTS_TIMEOUT)

        signal.setitimer(signal.ITIMER_REAL, TOX_RUN_TESTS_TIMEOUT)
        signal.signal(signal.SIGALRM, handle_timeout)
        LOG.debug(f'Run tests timeout set as {TOX_RUN_TESTS_TIMEOUT} seconds')


def terminate_childs():
    current_process = psutil.Process()
    children = current_process.children(recursive=False)
    for child in children:
        LOG.debug(f"Interrupt child process execution (pid={child.pid})")
        os.kill(child.pid, signal.SIGINT)
    for child in children:
        LOG.debug("Wait for top-child process termination "
                  f"(pid={child.pid})...")
        os.waitpid(child.pid, 0)


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
                   capture_stdout=False,
                   check=False)


def debug_test_cases():
    common.execute_python('-m testtools.run {posargs}',
                          posargs=common.get_posargs(),
                          capture_stdout=False)


def run_test_cases():
    common.execute('stestr run {posargs}',
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
