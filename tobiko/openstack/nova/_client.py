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

import time

from novaclient import client as novaclient
from novaclient.v2 import client as client_v2
from oslo_log import log

import tobiko
from tobiko.openstack import _client


CLIENT_CLASSES = (client_v2.Client,)
LOG = log.getLogger(__name__)


class NovaClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        return novaclient.Client('2', session=session)


class NovaClientManager(_client.OpenstackClientManager):

    def create_client(self, session):
        return NovaClientFixture(session=session)


CLIENTS = NovaClientManager()


def nova_client(obj):
    if not obj:
        return get_nova_client()

    if isinstance(obj, CLIENT_CLASSES):
        return obj

    fixture = tobiko.setup_fixture(obj)
    if isinstance(fixture, NovaClientFixture):
        return fixture.client

    message = "Object {!r} is not a NovaClientFixture".format(obj)
    raise TypeError(message)


def get_nova_client(session=None, shared=True, init_client=None,
                    manager=None):
    manager = manager or CLIENTS
    client = manager.get_client(session=session, shared=shared,
                                init_client=init_client)
    tobiko.setup_fixture(client)
    return client.client


def list_hypervisors(client=None, detailed=True, **params):
    client = nova_client(client)
    hypervisors = client.hypervisors.list(detailed=detailed)
    return tobiko.select(hypervisors).with_attributes(**params)


def find_hypervisor(client=None, unique=False, **params):
    hypervisors = list_hypervisors(client=client, **params)
    if unique:
        return hypervisors.unique
    else:
        return hypervisors.first


def list_servers(client=None, **params):
    client = nova_client(client)
    servers = client.servers.list()
    return tobiko.select(servers).with_attributes(**params)


def find_server(client=None, unique=False, **params):
    servers = list_servers(client=client, **params)
    if unique:
        return servers.unique
    else:
        return servers.first


def get_server(server, client=None):
    return nova_client(client).servers.get(server)


def get_console_output(server, timeout=None, interval=1., length=None,
                       client=None):
    client = nova_client(client)
    start_time = time.time()
    while True:
        try:
            output = client.servers.get_console_output(server=server,
                                                       length=length)
        except TypeError:
            # For some reason it could happen resulting body cannot be
            # translated to json object and it is converted to None
            # on such case get_console_output would raise a TypeError
            return None

        if timeout is None or output:
            break

        if time.time() - start_time > timeout:
            LOG.warning("No console output produced by server (%r) after "
                        "%r seconds", server, timeout)
            break

        LOG.debug('Waiting for server (%r) console output...', server)
        time.sleep(interval)

    return output
