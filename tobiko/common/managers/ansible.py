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

from oslo_log import log

from tobiko.common import constants


LOG = log.getLogger(__name__)


class AnsibleManager(object):
    """Manages Ansible entities."""

    def __init__(self, client_manager, templates_dir):
        self.client_manager = client_manager.heat_client
        self.playbooks_dir = templates_dir

    def get_playbooks_names(self, strip_suffix=False):
        """Returns a list of all the files in playbooks dir."""
        playbooks = []
        for (_, _, files) in os.walk(self.playbooks_dir):
            playbooks.extend(files)
        if strip_suffix:
            playbooks = [
                f[:-len(constants.TEMPLATE_SUFFIX)] for f in playbooks]
        return playbooks
