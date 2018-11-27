# Copyright (c) 2018 Red Hat
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

import os

from tobiko.common import clients
from tobiko.common.managers import stack


class TobikoCMD(object):
    """Manages different command line utilities."""

    def __init__(self):
        self.clientManager = clients.ClientManager()
        curr_dir = os.path.dirname(__file__)
        self.templates_dir = os.path.join(curr_dir,
                                          "../tests/scenario/templates")
        self.stackManager = stack.StackManager(self.clientManager,
                                               self.templates_dir)
