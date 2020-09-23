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


def list_services(client=None, **params) -> tobiko.Selection:
    client = nova_client(client)
    services = client.services.list()
    return tobiko.select(services).with_attributes(**params)


def find_service(client=None, unique=False, **params):
    services = list_services(client=client, **params)
    if unique:
        return services.unique
    else:
        return services.first


def get_server_id(server):
    if isinstance(server, str):
        return server
    else:
        return server.id


def get_server(server, client=None, **params):
    server_id = get_server_id(server)
    return nova_client(client).servers.get(server_id, **params)


def migrate_server(server, client=None, **params):
    # pylint: disable=protected-access
    server_id = get_server_id(server)
    LOG.debug(f"Start server migration (server_id='{server_id}', "
              f"info={params})")
    return nova_client(client).servers._action('migrate', server_id,
                                               info=params)


def confirm_resize(server, client=None, **params):
    server_id = get_server_id(server)
    LOG.debug(f"Confirm server resize (server_id='{server_id}', "
              f"info={params})")
    return nova_client(client).servers.confirm_resize(server_id, **params)


MAX_SERVER_CONSOLE_OUTPUT_LENGTH = 1024 * 256


def get_console_output(server, timeout=None, interval=1., length=None,
                       client=None):
    client = nova_client(client)
    start_time = time.time()
    if length is not None:
        length = min(length, MAX_SERVER_CONSOLE_OUTPUT_LENGTH)
    else:
        length = MAX_SERVER_CONSOLE_OUTPUT_LENGTH
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


class HasNovaClientMixin(object):

    nova_client = None

    def get_server(self, server, **params):
        return get_server(server=server, client=self.nova_client, **params)

    def get_server_console_output(self, server, **params):
        return get_console_output(server=server, client=self.nova_client,
                                  **params)


class WaitForServerStatusError(tobiko.TobikoException):
    message = ("Server {server_id} not changing status from {server_status} "
               "to {status}")


class WaitForServerStatusTimeout(WaitForServerStatusError):
    message = ("Server {server_id} didn't change its status from "
               "{server_status} to {status} status after {timeout} seconds")


NOVA_SERVER_TRANSIENT_STATUS = {
    'ACTIVE': ('BUILD', 'SHUTOFF'),
    'SHUTOFF': ('ACTIVE'),
    'VERIFY_RESIZE': ('RESIZE'),
}


def wait_for_server_status(server, status, client=None, timeout=None,
                           sleep_time=None, transient_status=None):
    if timeout is None:
        timeout = 300.
    if sleep_time is None:
        sleep_time = 5.
    start_time = time.time()
    if transient_status is None:
        transient_status = NOVA_SERVER_TRANSIENT_STATUS.get(status) or tuple()
    while True:
        server = get_server(server=server, client=client)
        if server.status == status:
            break

        if server.status not in transient_status:
            raise WaitForServerStatusError(server_id=server.id,
                                           server_status=server.status,
                                           status=status)

        if time.time() - start_time >= timeout:
            raise WaitForServerStatusTimeout(server_id=server.id,
                                             server_status=server.status,
                                             status=status,
                                             timeout=timeout)

        progress = getattr(server, 'progress', None)
        LOG.debug(f"Waiting for server {server.id} status to get from "
                  f"{server.status} to {status} "
                  f"(progress={progress}%)")
        time.sleep(sleep_time)
    return server


def shutoff_server(server, client=None, timeout=None, sleep_time=None):
    client = nova_client(client)
    server = get_server(server=server, client=client)
    if server.status == 'SHUTOFF':
        return server

    client.servers.stop(server.id)
    return wait_for_server_status(server=server.id, status='SHUTOFF',
                                  client=client, timeout=timeout,
                                  sleep_time=sleep_time)


def activate_server(server, client=None, timeout=None, sleep_time=None):
    client = nova_client(client)
    server = get_server(server=server, client=client)
    if server.status == 'ACTIVE':
        return server

    if server.status == 'SHUTOFF':
        client.servers.start(server.id)
    elif server.status == 'RESIZE':
        wait_for_server_status(server=server.id, status='VERIFY_RESIZE',
                               client=client, timeout=timeout,
                               sleep_time=sleep_time)
        client.servers.confirm_resize(server)
    elif server.status == 'VERIFY_RESIZE':
        client.servers.confirm_resize(server)
    else:
        client.servers.reboot(server.id, reboot_type='HARD')

    return wait_for_server_status(server=server.id, status='ACTIVE',
                                  client=client, timeout=timeout,
                                  sleep_time=sleep_time)
