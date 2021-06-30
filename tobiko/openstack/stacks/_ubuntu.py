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

import typing

import tobiko
from tobiko import config
from tobiko.openstack import glance
from tobiko.openstack.stacks import _nova


CONF = config.CONF

UBUNTU_IMAGE_VERSION = 'focal'

UBUNTU_IMAGE_VERSION_NUMBER = '20.04'

UBUNTU_MINIMAL_IMAGE_URL = (
    'https://cloud-images.ubuntu.com/minimal/releases/'
    f'{UBUNTU_IMAGE_VERSION}/release/'
    f'ubuntu-{UBUNTU_IMAGE_VERSION_NUMBER}-minimal-cloudimg-amd64.img')


class UbuntuMinimalImageFixture(glance.URLGlanceImageFixture):
    image_url = CONF.tobiko.ubuntu.image_url or UBUNTU_MINIMAL_IMAGE_URL
    image_name = CONF.tobiko.ubuntu.image_name
    image_file = CONF.tobiko.ubuntu.image_file
    disk_format = CONF.tobiko.ubuntu.disk_format or "qcow2"
    container_format = CONF.tobiko.ubuntu.container_format or "bare"
    username = CONF.tobiko.ubuntu.username or 'ubuntu'
    password = CONF.tobiko.ubuntu.password
    connection_timeout = CONF.tobiko.ubuntu.connection_timeout or 600.


IPERF3_SERVICE_FILE = """
[Unit]
Description=iperf3 server on port %i
After=syslog.target network.target

[Service]
ExecStart=/usr/bin/iperf3 -s -p %i
Restart=always
RuntimeMaxSec=3600
User=root

[Install]
WantedBy=multi-user.target
DefaultInstance=5201
"""


class UbuntuImageFixture(UbuntuMinimalImageFixture,
                         glance.CustomizedGlanceImageFixture):
    """Ubuntu server image running an HTTP server

    The server has additional installed packages compared to
    the minimal one:
      - iperf3
      - ping
      - ncat
      - nginx

    The image will also have below running services:
      - nginx HTTP server listening on TCP port 80
      - iperf3 server listening on TCP port 5201
    """

    @property
    def firstboot_commands(self) -> typing.List[str]:
        return super().firstboot_commands + [
            'sh -c "hostname > /var/www/html/id"']

    @property
    def install_packages(self) -> typing.List[str]:
        return super().install_packages + ['iperf3',
                                           'iputils-ping',
                                           'ncat',
                                           'nginx']

    # port of running HTTP server
    http_port = 80

    # port of running Iperf3 server
    iperf3_port = 5201

    @property
    def run_commands(self) -> typing.List[str]:
        run_commands = super().run_commands
        run_commands.append(
            f'echo "{IPERF3_SERVICE_FILE}" '
            '> /etc/systemd/system/iperf3-server@.service')
        run_commands.append(
            f"systemctl enable iperf3-server@{self.iperf3_port}")
        return run_commands


class UbuntuFlavorStackFixture(_nova.FlavorStackFixture):
    ram = 128
    swap = 512


class UbuntuMinimalServerStackFixture(_nova.CloudInitServerStackFixture):

    #: Glance image used to create a Nova server instance
    image_fixture = tobiko.required_setup_fixture(UbuntuMinimalImageFixture)

    #: Flavor used to create a Nova server instance
    flavor_stack = tobiko.required_setup_fixture(UbuntuFlavorStackFixture)


class UbuntuServerStackFixture(UbuntuMinimalServerStackFixture):
    """Ubuntu server running an HTTP server

    The server has additional commands compared to the minimal one:
      iperf3
      ping
    """

    #: Glance image used to create a Nova server instance
    image_fixture = tobiko.required_setup_fixture(UbuntuImageFixture)

    # port of running HTTP server
    @property
    def http_port(self) -> int:
        return self.image_fixture.http_port

    @property
    def iperf3_port(self) -> int:
        return self.image_fixture.iperf3_port


class UbuntuExternalServerStackFixture(UbuntuServerStackFixture,
                                       _nova.ExternalServerStackFixture):
    """Ubuntu server with port on special external network
    """
