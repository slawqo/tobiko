# Copyright (c) 2022 Red Hat, Inc.
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

from oslo_log import log
import testtools

from tobiko.openstack import neutron
from tobiko import tripleo
from tobiko.tripleo import pacemaker
from tobiko.tripleo import processes


LOG = log.getLogger(__name__)


@tripleo.skip_if_missing_overcloud
class PacemakerTest(testtools.TestCase):

    def test_resources_health(self):
        """Check cluster failed statuses"""
        self.assertTrue(pacemaker.PacemakerResourcesStatus().all_healthy)


@tripleo.skip_if_missing_overcloud
class OvercloudProcessesTest(testtools.TestCase):

    def test_overcloud_processes_running(self):
        procs = processes.OvercloudProcessesStatus()
        self.assertTrue(procs.basic_overcloud_processes_running)

    @neutron.skip_unless_is_ovn()
    def test_ovn_overcloud_processes_validations(self):
        procs = processes.OvercloudProcessesStatus()
        self.assertTrue(procs.ovn_overcloud_processes_validations)
