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

from oslo_log import log
import os_faults

from tobiko.openstack.os_faults import _cloud


LOG = log.getLogger(__name__)


def os_faults_execute(command, cloud_management=None, config_filename=None,
                      **kwargs):
    cloud_management = (
        cloud_management or
        _cloud.get_os_fault_cloud_managenemt(
            config_filename=config_filename))
    if kwargs:
        command = command.format(**kwargs)
    return os_faults.human_api(cloud_management, command)
