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

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack.stacks import _centos
from tobiko.openstack.stacks import _cirros
from tobiko.openstack.stacks import _neutron
from tobiko.openstack.stacks import _nova
from tobiko.openstack.stacks import _ubuntu


@neutron.skip_if_missing_networking_extensions('l3-ha')
class L3haNetworkStackFixture(_neutron.NetworkStackFixture):
    ha = True


@neutron.skip_if_missing_networking_extensions('l3-ha')
class L3haServerStackFixture(_cirros.CirrosServerStackFixture):
    #: Heat stack for creating internal network with L3HA enabled
    network_stack = tobiko.required_setup_fixture(
        L3haNetworkStackFixture)


class L3haPeerServerStackFixture(
        L3haServerStackFixture, _nova.PeerServerStackFixture):
    peer_stack = tobiko.required_setup_fixture(L3haServerStackFixture)


class L3haSameHostServerStackFixture(
        L3haPeerServerStackFixture, _nova.SameHostServerStackFixture):
    pass


class L3haDifferentHostServerStackFixture(
        L3haPeerServerStackFixture, _nova.DifferentHostServerStackFixture):
    pass


class L3haCentosServerStackFixture(_centos.CentosServerStackFixture,
                                   L3haServerStackFixture):
    pass


class L3haUbuntuServerStackFixture(_ubuntu.UbuntuServerStackFixture,
                                   L3haServerStackFixture):
    pass
