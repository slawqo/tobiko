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

import os_faults
from oslo_log import log

import tobiko
from tobiko.openstack.os_faults import _config_file

LOG = log.getLogger(__name__)


def get_os_fault_cloud_managenemt(config_filename=None):
    fixture = OsFaultsCloudManagementFixture(config_filename=config_filename)
    return tobiko.setup_fixture(fixture).cloud_management


class OsFaultsCloudManagementFixture(tobiko.SharedFixture):
    """Responsible for executing faults."""

    config_filename = None
    cloud_management = None

    def __init__(self, config_filename=None, cloud_management=None):
        super(OsFaultsCloudManagementFixture, self).__init__()
        if config_filename:
            self.config_filename = config_filename
        if cloud_management:
            self.cloud_management = cloud_management

    def setup_fixture(self):
        self.connect()

    def connect(self):
        """Connect to the cloud using os-faults."""
        cloud_management = self.cloud_management
        if cloud_management is None:
            config_filename = self.config_filename
            if config_filename is None:
                self.config_filename = config_filename = (
                    _config_file.get_os_fault_config_filename())
            LOG.info("OS-Faults: connecting with config filename %s",
                     config_filename)
            self.cloud_management = cloud_management = os_faults.connect(
                config_filename=config_filename)
        return cloud_management
