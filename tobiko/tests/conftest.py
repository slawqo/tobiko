# Copyright (c) 2020 Red Hat
# All Rights Reserved.
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

from datetime import datetime
import os
import subprocess

from oslo_log import log
from py.xml import html  # pylint: disable=no-name-in-module,import-error
import pytest


LOG = log.getLogger(__name__)

TOX_REPORT_NAME = os.environ.get('TOX_REPORT_NAME', "tobiko_results")


@pytest.hookimpl
def pytest_configure(config):
    configure_metadata(config)
    configure_caplog(config)
    configure_timeout(config)
    configure_junitxml(config)


def configure_metadata(config):
    # pylint: disable=protected-access
    from tobiko import version
    config._metadata["Tobiko Version"] = version.release
    git_commit = subprocess.check_output(
        ['git', 'log', '-n', '1'],
        universal_newlines=True).replace('\n', '<br>')
    config._metadata["Tobiko Git Commit"] = git_commit


def configure_caplog(config):
    import tobiko
    tobiko_config = tobiko.tobiko_config()

    if tobiko_config.logging.capture_log is True:
        if tobiko_config.debug:
            default = 'DEBUG'
        else:
            default = 'INFO'
    else:
        default = 'FATAL'
    for key in ['log_level',
                'log_file_level',
                'log_cli_level']:
        set_default_inicfg(config, key, default)

    default = tobiko_config.logging_default_format_string
    if default:
        # instance and color are not supported by pytest
        default = default.replace('%(instance)s', '')
        default = default.replace('%(color)s', '')
        if default:
            for key in ['log_format',
                        'log_file_format',
                        'log_cli_format']:
                set_default_inicfg(config, key, default)

    default = tobiko_config.log_date_format
    if default:
        for key in ['log_date_format',
                    'log_file_date_format',
                    'log_cli_date_format']:
            set_default_inicfg(config, key, default)


def configure_junitxml(config):
    config.inicfg['junit_suite_name'] = TOX_REPORT_NAME


def set_default_inicfg(config, key, default):
    value = config.inicfg.setdefault(key, default)
    if value != default:
        LOG.debug(f"Set default inicfg: {key} = {value}")
    else:
        LOG.debug(f"Keep existing inicfg: {key} = {value}")


def configure_timeout(config):
    import tobiko
    tobiko_config = tobiko.tobiko_config()
    default = tobiko_config.testcase.timeout
    if default is not None and default > 0.:
        set_default_inicfg(config, 'timeout', default)


def pytest_html_results_table_header(cells):
    cells.insert(2, html.th("Description"))
    cells.insert(1, html.th("Time", class_="sortable time", col="time"))
    cells.pop()


def pytest_html_results_table_row(report, cells):
    cells.insert(2, html.td(report.description))
    cells.insert(1, html.td(datetime.utcnow(), class_="col-time"))
    cells.pop()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):  # pylint: disable=unused-argument
    outcome = yield
    report = outcome.get_result()
    report.description = str(item.function.__doc__)


def pytest_html_report_title(report):
    report.title = f"Tobiko test results ({TOX_REPORT_NAME})"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    # pylint: disable=protected-access
    import tobiko
    tobiko.push_test_case(item._testcase)
    try:
        yield
    finally:
        tobiko.pop_test_case()
