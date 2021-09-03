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

from octaviaclient.api.v2 import octavia

import tobiko
from tobiko.openstack import _client
from tobiko.openstack import keystone
from tobiko.openstack import nova
from tobiko.openstack import topology


OCTAVIA_CLIENT_CLASSSES = octavia.OctaviaAPI,


def get_octavia_endpoint(keystone_client=None):
    return keystone.find_service_endpoint(name='octavia',
                                          client=keystone_client)


class OctaviaClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        keystone_client = keystone.get_keystone_client(session=session)
        endpoint = get_octavia_endpoint(keystone_client=keystone_client)
        return octavia.OctaviaAPI(session=session, endpoint=endpoint.url)


class OctaviaClientManager(_client.OpenstackClientManager):

    def create_client(self, session):
        return OctaviaClientFixture(session=session)


CLIENTS = OctaviaClientManager()


def octavia_client(obj):
    if not obj:
        return get_octavia_client()

    if isinstance(obj, OCTAVIA_CLIENT_CLASSSES):
        return obj

    fixture = tobiko.setup_fixture(obj)
    if isinstance(fixture, OctaviaClientFixture):
        return fixture.client

    message = "Object {!r} is not an OctaviaClientFixture".format(obj)
    raise TypeError(message)


def get_octavia_client(session=None, shared=True, init_client=None,
                       manager=None):
    manager = manager or CLIENTS
    client = manager.get_client(session=session, shared=shared,
                                init_client=init_client)
    tobiko.setup_fixture(client)
    return client.client


def get_loadbalancer(loadbalancer_id, client=None):
    return octavia_client(client).load_balancer_show(lb_id=loadbalancer_id)


def get_member(pool_id, member_id, client=None):
    return octavia_client(client).member_show(pool_id=pool_id,
                                              member_id=member_id)


def list_amphorae(loadbalancer_id: str, client=None):
    return octavia_client(client).amphora_list(
        loadbalancer_id=loadbalancer_id)['amphorae']


def list_amphoras_compute_nodes(load_balancer_id: str, client=None):
    """List the compute nodes which host the LB amphoras

    This function finds the Overcloud compute nodes which
    host the amphoras and returns a list of their instances.
    """

    hostnames = set()
    for amphora in list_amphorae(loadbalancer_id=load_balancer_id,
                                 client=client):
        server = nova.get_server(amphora['compute_id'])
        hostnames.add(getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname'))
    return list(hostnames)


def get_amphoras_compute_nodes(load_balancer_id: str, client=None):
    """Gets the hostnames/compute nodes which host the LB amphoras

    This function finds the Overcloud compute nodes which
    host the amphoras and returns a list of their instances.
    """

    hostnames = list_amphoras_compute_nodes(load_balancer_id=load_balancer_id,
                                            client=client)
    return topology.list_openstack_nodes(hostnames=hostnames)


def get_amphora_vm(
        loadbalancer_id: str, client=None) -> typing.Optional[nova.NovaServer]:

    """Gets the LB's amphora virtual machine.

    When the Octavia's topology is SINGLE, it returns
    the amphora's only vm.
    When the Octavia's topology is ACTIVE_STANDBY,
    it returns the first amphora's vm.
    It might be MASTER or BACKUP.
    """

    amphora_vm_id = list_amphorae(loadbalancer_id, client)[0]['compute_id']

    err_msg = ("Could not find amphora_vm_id for any amphora in " +
               f"LB {loadbalancer_id}")
    tobiko_test_case = tobiko.get_test_case()
    tobiko_test_case.assertTrue(amphora_vm_id, err_msg)

    return nova.get_server(server_id=amphora_vm_id)
