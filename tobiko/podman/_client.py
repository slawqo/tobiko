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

import six

import podman

import tobiko
from tobiko.podman import _exception
from tobiko.podman import _shell
from tobiko.shell import ssh


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
        if six.PY2:
            raise _exception.PodmanError(
                "Podman isn't compatible with python 2.7")
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
        client = self.client
        if client is None:
            self.client = client = self.create_client()
        return client

    def create_client(self):
        podman_remote_socket = self.discover_podman_socket()
        remote_uri = 'ssh://{username}@{host}{socket}'.format(
            username=self.ssh_client.connect_parameters['username'],
            host=self.ssh_client.host,
            socket=podman_remote_socket)
        client = podman.Client(uri=podman_remote_socket,
                               remote_uri=remote_uri,
                               identity_file='~/.ssh/id_rsa')
        client.system.ping()
        return client

    def connect(self):
        return tobiko.setup_fixture(self).client

    def discover_podman_socket(self):
        return _shell.discover_podman_socket(ssh_client=self.ssh_client)
