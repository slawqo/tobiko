# Copyright (c) 2020 Red Hat, Inc.
#
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

import tobiko
from tobiko.shell.sh import _execute


class UptimeError(tobiko.TobikoException):
    message = "Unable to get uptime from host: {error}"


def get_uptime(**execute_params):
    """Returns the number of seconds passed since last host reboot

    It reads and parses remote special file /proc/uptime and returns a floating
    point value that represents the number of seconds passed since last host
    reboot
    """
    result = _execute.execute('cat /proc/uptime', stdin=False, stdout=True,
                              stderr=True, expect_exit_status=None,
                              **execute_params)
    output = result.stdout and result.stdout.strip()
    if result.exit_status or not output:
        raise UptimeError(error=result.stderr)

    uptime_line = output.splitlines()[0]
    uptime_string = uptime_line.split()[0]
    return float(uptime_string)
