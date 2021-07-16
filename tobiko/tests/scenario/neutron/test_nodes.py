# Copyright (c) 2021 Red Hat
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

import pytest
import testtools

from tobiko.openstack import neutron
from tobiko.openstack import tests


@neutron.skip_unless_is_ovn()
class NodeTest(testtools.TestCase):

    @pytest.mark.ovn_migration
    def test_ovs_namespaces_are_absent(self):
        tests.test_ovs_namespaces_are_absent()

    @pytest.mark.ovn_migration
    def test_ovs_interfaces_are_absent(self):
        tests.test_ovs_interfaces_are_absent()
