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

from octaviaclient.api.v2 import octavia

import tobiko
from tobiko.openstack import _client
from tobiko.openstack import keystone
from tobiko.openstack import nova
from tobiko.openstack.octavia import _validators
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


def get_loadbalancer(loadbalancer_id: str, client=None):
    return octavia_client(client).load_balancer_show(lb_id=loadbalancer_id)


def get_member(pool_id: str, member_id: str, client=None):
    return octavia_client(client).member_show(pool_id=pool_id,
                                              member_id=member_id)


def list_members(pool_id: str, client=None):
    return octavia_client(client).member_list(pool_id=pool_id)['members']


def list_amphorae(loadbalancer_id: str, client=None):
    return octavia_client(client).amphora_list(
        loadbalancer_id=loadbalancer_id)['amphorae']


def get_amphora_compute_node(loadbalancer_id: str,
                             lb_port: int,
                             lb_protocol: str,
                             ip_address: str) -> (
        topology.OpenStackTopologyNode):
    """Gets the compute node which hosts the LB amphora

    This function finds the Overcloud compute node which
    hosts the amphora. In case there are more than 1 amphora
    (e.g. if the LB's topology is Active/standby), so the compute node which
    hosts the master amphora will be returned.

    :param loadbalancer_id (str): The loadbalancer ID.
    :param lb_port (int): The loadbalancer port.
    :param lb_protocol (str): The loadbalancer protocol.
    :param ip_address (str): The ip adress of the loadbalancer.
    :return (TripleoTopologyNode): The compute node which hosts the Amphora.
    """

    amphorae = list_amphorae(loadbalancer_id)
    if len(amphorae) > 1:  # For a high available LB
        amphora = get_master_amphora(amphorae=amphorae,
                                     lb_port=lb_port,
                                     lb_protocol=lb_protocol,
                                     ip_address=ip_address)
    else:
        amphora = amphorae[0]

    server = nova.get_server(amphora['compute_id'])
    hostname = getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname')
    return topology.get_openstack_node(hostname=hostname)


def get_master_amphora(amphorae: dict,
                       lb_port: int,
                       lb_protocol: str,
                       ip_address: str,
                       client=None) -> dict:
    """Gets the master Amphora in a High Available LB
    (a loadbalancer which uses the Active/standby topology)

    :param amphorae (dict): The list of amphoras (each represented by
     JSON).
    :param lb_port (int): The loadbalancer port.
    :param lb_protocol (str): The loadbalancer protocol.
    :param ip_address (str): The ip adress of the loadbalancer.
    :param client (optional): Any client with access to the Octavia APIs.
    :return amphora (dict): JSON of the Master Amphora.
    """

    # Generate traffic on the LB so we can identify the current Master
    _validators.check_members_balanced(
        ip_address=ip_address,
        protocol=lb_protocol,
        port=lb_port,
        members_count=1,
        requests_count=1)

    # The amphora which has total_connections > 0 is the master.
    # Backup amphora will always have total_connections == 0.
    for amphora in amphorae:
        amphora_stats = octavia_client(client).amphora_stats_show(
            amphora['id'])
        for listener in list(amphora_stats.values())[0]:
            if listener['total_connections'] > 0:
                return amphora

    raise ValueError("Master Amphora wasn't found!")
