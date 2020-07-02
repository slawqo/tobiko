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

import podman

import tobiko
from tobiko.podman import _exception
from tobiko.podman import _shell
from tobiko.shell import ssh
from tobiko.shell import sh


def get_podman_client(ssh_client=None):
    return PodmanClientFixture(ssh_client=ssh_client)


def list_podman_containers(client=None, **kwargs):
    try:
        containers = podman_client(client).containers.list(**kwargs)
    except _exception.PodmanSocketNotFoundError:
        return tobiko.Selection()
    else:
        return tobiko.select(containers)


def podman_client(obj=None):
    if obj is None:
        obj = get_podman_client()
    if tobiko.is_fixture(obj):
        obj = tobiko.setup_fixture(obj).client
    if isinstance(obj, podman.Client):
        return obj
    raise TypeError('Cannot obtain a Podman client from {!r}'.format(obj))


class PodmanClientFixture(tobiko.SharedFixture):

    client = None
    ssh_client = None

    def __init__(self, ssh_client=None):
        super(PodmanClientFixture, self).__init__()
        if ssh_client:
            self.ssh_client = ssh_client

    def setup_fixture(self):
        self.setup_ssh_client()
        self.setup_client()

    def setup_ssh_client(self):
        ssh_client = self.ssh_client
        if ssh_client is None:
            self.ssh_client = ssh_client = ssh.ssh_proxy_client() or False
            if ssh_client:
                tobiko.setup_fixture(ssh_client)
        return ssh_client

    def setup_client(self):
        # setup podman access via varlink
        podman_client_setup_cmds = \
            "sudo test -f /var/varlink_client_access_setup ||  \
            (sudo groupadd -f podman &&  \
            sudo usermod -a -G podman heat-admin && \
            sudo chmod -R o=wxr /etc/tmpfiles.d && \
            sudo echo 'd /run/podman 0770 root heat-admin' >  \
            /etc/tmpfiles.d/podman.conf && \
            sudo cp /lib/systemd/system/io.podman.socket \
            /etc/systemd/system/io.podman.socket && \
            sudo crudini --set /etc/systemd/system/io.podman.socket Socket  \
            SocketMode 0660 && \
            sudo crudini --set /etc/systemd/system/io.podman.socket Socket  \
            SocketGroup podman && \
            sudo systemctl daemon-reload && \
            sudo systemd-tmpfiles --create && \
            sudo systemctl enable --now io.podman.socket && \
            sudo chmod 777 /run/podman && \
            sudo chown -R root: /run/podman && \
            sudo chmod g+rw /run/podman/io.podman && \
            sudo chmod 777 /run/podman/io.podman && \
            sudo setenforce 0 && \
            sudo systemctl start io.podman.socket && \
            sudo touch /var/varlink_client_access_setup)"

        sh.execute(podman_client_setup_cmds, ssh_client=self.ssh_client)

        client = self.client
        if client is None:
            self.client = client = self.create_client()
        return client

    def create_client(self):
        for _ in range(360):

            try:
                podman_remote_socket = self.discover_podman_socket()
                username = self.ssh_client.connect_parameters['username']
                host = self.ssh_client.connect_parameters["hostname"]
                socket = podman_remote_socket
                podman_remote_socket_uri = \
                    'unix:/tmp/podman.sock_{}'.format(host)

                remote_uri = 'ssh://{username}@{host}{socket}'.format(
                    username=username,
                    host=host,
                    socket=socket)

                client = podman.Client(uri=podman_remote_socket_uri,
                                       remote_uri=remote_uri,
                                       identity_file='~/.ssh/id_rsa')
                client.system.ping()
                return client
            except (ConnectionRefusedError, ConnectionResetError):
                # retry
                self.create_client()

    def connect(self):
        return tobiko.setup_fixture(self).client

    def discover_podman_socket(self):
        return _shell.discover_podman_socket(ssh_client=self.ssh_client)
