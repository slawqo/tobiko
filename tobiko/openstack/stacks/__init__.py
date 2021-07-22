# Copyright (c) 2019 Red Hat, Inc.
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

from tobiko.openstack.stacks import _centos
from tobiko.openstack.stacks import _cirros
from tobiko.openstack.stacks import _fedora
from tobiko.openstack.stacks import _redhat
from tobiko.openstack.stacks import _l3ha
from tobiko.openstack.stacks import _neutron
from tobiko.openstack.stacks import _nova
from tobiko.openstack.stacks import _octavia
from tobiko.openstack.stacks import _qos
from tobiko.openstack.stacks import _ubuntu

CentosFlavorStackFixture = _centos.CentosFlavorStackFixture
CentosImageFixture = _centos.CentosImageFixture
CentosServerStackFixture = _centos.CentosServerStackFixture
Centos7ServerStackFixture = _centos.Centos7ServerStackFixture

CirrosFlavorStackFixture = _cirros.CirrosFlavorStackFixture
CirrosImageFixture = _cirros.CirrosImageFixture
CirrosServerStackFixture = _cirros.CirrosServerStackFixture
CirrosPeerServerStackFixture = _cirros.CirrosPeerServerStackFixture
CirrosDifferentHostServerStackFixture = (
    _cirros.CirrosDifferentHostServerStackFixture)
CirrosSameHostServerStackFixture = _cirros.CirrosSameHostServerStackFixture
RebootCirrosServerOperation = _cirros.RebootCirrosServerOperation
EvacuableCirrosImageFixture = _cirros.EvacuableCirrosImageFixture
EvacuableServerStackFixture = _cirros.EvacuableServerStackFixture
CirrosHttpServerStackFixture = _cirros.CirrosHttpServerStackFixture

FedoraFlavorStackFixture = _fedora.FedoraFlavorStackFixture
FedoraImageFixture = _fedora.FedoraImageFixture
FedoraServerStackFixture = _fedora.FedoraServerStackFixture

RedHatFlavorStackFixture = _redhat.RedHatFlavorStackFixture
RhelImageFixture = _redhat.RhelImageFixture
RedHatServerStackFixture = _redhat.RedHatServerStackFixture

L3haNetworkStackFixture = _l3ha.L3haNetworkStackFixture
L3haServerStackFixture = _l3ha.L3haServerStackFixture
L3haPeerServerStackFixture = _l3ha.L3haPeerServerStackFixture
L3haDifferentHostServerStackFixture = _l3ha.L3haDifferentHostServerStackFixture
L3haSameHostServerStackFixture = _l3ha.L3haSameHostServerStackFixture

NetworkStackFixture = _neutron.NetworkStackFixture
FloatingNetworkStackFixture = _neutron.FloatingNetworkStackFixture
NetworkWithNetMtuWriteStackFixture = (
    _neutron.NetworkWithNetMtuWriteStackFixture)
SecurityGroupsFixture = _neutron.SecurityGroupsFixture

get_external_network = _neutron.get_external_network
has_external_network = _neutron.has_external_network
skip_unless_has_external_network = _neutron.skip_unless_has_external_network
get_floating_network = _neutron.get_floating_network
has_floating_network = _neutron.has_floating_network
skip_unless_has_floating_network = _neutron.skip_unless_has_floating_network

ServerStackFixture = _nova.ServerStackFixture
KeyPairStackFixture = _nova.KeyPairStackFixture
FlavorStackFixture = _nova.FlavorStackFixture
ServerGroupStackFixture = _nova.ServerGroupStackFixture
AffinityServerGroupStackFixture = _nova.AffinityServerGroupStackFixture
AntiAffinityServerGroupStackFixture = _nova.AntiAffinityServerGroupStackFixture

QosNetworkStackFixture = _qos.QosNetworkStackFixture
QosPolicyStackFixture = _qos.QosPolicyStackFixture
QosServerStackFixture = _qos.QosServerStackFixture

UbuntuFlavorStackFixture = _ubuntu.UbuntuFlavorStackFixture
UbuntuImageFixture = _ubuntu.UbuntuImageFixture
UbuntuMinimalImageFixture = _ubuntu.UbuntuMinimalImageFixture
UbuntuServerStackFixture = _ubuntu.UbuntuServerStackFixture
UbuntuMinimalServerStackFixture = _ubuntu.UbuntuMinimalServerStackFixture
UbuntuExternalServerStackFixture = _ubuntu.UbuntuExternalServerStackFixture

OctaviaLoadbalancerStackFixture = _octavia.OctaviaLoadbalancerStackFixture
OctaviaListenerStackFixture = _octavia.OctaviaListenerStackFixture
OctaviaPoolStackFixture = _octavia.OctaviaPoolStackFixture
OctaviaMemberServerStackFixture = _octavia.OctaviaMemberServerStackFixture
OctaviaServerStackFixture = _octavia.OctaviaServerStackFixture
OctaviaClientServerStackFixture = _octavia.OctaviaClientServerStackFixture
OctaviaOtherServerStackFixture = _octavia.OctaviaOtherServerStackFixture
OctaviaOtherMemberServerStackFixture = (
    _octavia.OctaviaOtherMemberServerStackFixture)
