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

from tobiko import config
from tobiko.openstack import glance
from tobiko.openstack.stacks import _nova
from tobiko.shell import sh
import tobiko.tripleo


CONF = config.CONF

CIRROS_IMAGE_VERSION = '0.5.2'

if tobiko.tripleo.has_undercloud():
    CIRROS_IMAGE_URL = (
        f"http://rhos-qe-mirror-rdu2.usersys.redhat.com/images/cirros-"
        f"{CIRROS_IMAGE_VERSION}-x86_64-disk.img")

else:
    CIRROS_IMAGE_URL = (
        'http://download.cirros-cloud.net/{version}/'
        'cirros-{version}-x86_64-disk.img').format(
        version=CIRROS_IMAGE_VERSION)


class CirrosImageFixture(glance.URLGlanceImageFixture):

    image_url = CONF.tobiko.cirros.image_url or CIRROS_IMAGE_URL
    image_name = CONF.tobiko.cirros.image_name
    image_file = CONF.tobiko.cirros.image_file
    container_format = CONF.tobiko.cirros.container_format or "bare"
    disk_format = CONF.tobiko.cirros.disk_format or "qcow2"
    username = CONF.tobiko.cirros.username or 'cirros'
    password = CONF.tobiko.cirros.password or 'gocubsgo'
    connection_timeout = CONF.tobiko.cirros.connection_timeout or 200.


class CirrosFlavorStackFixture(_nova.FlavorStackFixture):
    ram = 128


class CirrosServerStackFixture(_nova.ServerStackFixture):

    #: Glance image used to create a Nova server instance
    image_fixture = tobiko.required_fixture(CirrosImageFixture)

    #: Flavor used to create a Nova server instance
    flavor_stack = tobiko.required_fixture(CirrosFlavorStackFixture)

    #: CirrOS can't get IP addresses from config-drive
    need_dhcp = True

    #: We expect CirrOS based servers to be fast to boot
    is_reachable_timeout: tobiko.Seconds = 300.


class CirrosPeerServerStackFixture(CirrosServerStackFixture,
                                   _nova.PeerServerStackFixture):
    #: Peer server used to reach this one
    peer_stack = tobiko.required_fixture(CirrosServerStackFixture)


class CirrosSameHostServerStackFixture(
        CirrosPeerServerStackFixture, _nova.SameHostServerStackFixture):
    pass


class CirrosDifferentHostServerStackFixture(
        CirrosPeerServerStackFixture, _nova.DifferentHostServerStackFixture):
    pass


class RebootCirrosServerOperation(sh.RebootHostOperation):

    stack = tobiko.required_fixture(CirrosServerStackFixture)

    @property
    def ssh_client(self):
        return self.stack.ssh_client


class EvacuableCirrosImageFixture(CirrosImageFixture):

    tags = ['evacuable']


class EvacuableServerStackFixture(CirrosServerStackFixture):

    #: Glance image used to create a Nova server instance
    image_fixture = tobiko.required_fixture(EvacuableCirrosImageFixture)


class ExtraDhcpOptsCirrosServerStackFixture(CirrosServerStackFixture):
    use_extra_dhcp_opts = True
