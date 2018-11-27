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
import signal

import tobiko.common.exceptions as exc


def kill_process(pid_num=None, pid_f=None):
    if not any([pid_num, pid_f]):
        raise exc.MissingInputException("pid")
    elif pid_num:
        os.kill(int(pid_num), signal.SIGINT)
    else:
        with open(pid_f) as f:
            pid = f.read()
            os.kill(int(pid), signal.SIGINT)
