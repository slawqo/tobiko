# Copyright 2022 Red Hat
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
from tobiko.openstack.octavia import _client
from tobiko.openstack.octavia import _load_balancer
from tobiko.openstack import nova
from tobiko.openstack.octavia import _validators
from tobiko.openstack import topology


AmphoraType = typing.Dict[str, typing.Any]
AmphoraIdType = typing.Union[str, AmphoraType]


def get_amphora_id(amphora: AmphoraIdType) -> str:
    if isinstance(amphora, str):
        return amphora
    else:
        return amphora['id']


def get_amphora(amphora: AmphoraIdType,
                client: _client.OctaviaClientType = None) -> AmphoraType:
    amphora_id = get_amphora_id(amphora)
    return _client.octavia_client(client).amphora_show(amphora_id)['amphora']


def list_amphorae(load_balancer: _load_balancer.LoadBalancerIdType = None,
                  client: _client.OctaviaClientType = None,
                  **params) \
        -> tobiko.Selection[AmphoraType]:
    if load_balancer is not None:
        params['load_balancer_id'] = _load_balancer.get_load_balancer_id(
            load_balancer)
    amphorae = _client.octavia_client(client).amphora_list(
        **params)['amphorae']
    return tobiko.select(amphorae)


def get_amphora_compute_node(load_balancer: _load_balancer.LoadBalancerIdType,
                             port: int,
                             protocol: str,
                             ip_address: str,
                             client: _client.OctaviaClientType = None) -> (
        topology.OpenStackTopologyNode):
    """Gets the compute node which hosts the LB amphora

    This function finds the Overcloud compute node which
    hosts the amphora. In case there are more than 1 amphora
    (e.g. if the LB's topology is Active/standby), so the compute node which
    hosts the master amphora will be returned.

    :param load_balancer: the load balancer ID.
    :param port: the load balancer port.
    :param protocol: the load balancer protocol.
    :param ip_address: the IP address of the load balancer
    :param client: the Octavia client
    :return: the compute node which hosts the Amphora.
    """
    amphorae = list_amphorae(load_balancer)
    amphora = get_master_amphora(amphorae=amphorae,
                                 port=port,
                                 protocol=protocol,
                                 ip_address=ip_address,
                                 client=client)
    server = nova.get_server(amphora['compute_id'])
    hostname = getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname')
    return topology.get_openstack_node(hostname=hostname)


def get_master_amphora(amphorae: typing.Iterable[AmphoraType],
                       port: int,
                       protocol: str,
                       ip_address: str,
                       client=None) -> AmphoraType:
    """Gets the master Amphora in a High Available LB
    (a loadbalancer which uses the Active/standby topology)

    :param amphorae: The list of amphoras (each represented by
     JSON).
    :param port: the load balancer port.
    :param protocol: the load balancer protocol.
    :param ip_address: the IP address of the load balancer
    :param client: the Octavia client
    :return amphora (dict): JSON of the Master Amphora.
    """

    amphorae = tobiko.select(amphorae)
    try:
        return amphorae.unique
    except tobiko.MultipleObjectsFound:
        # For a high available LB
        pass

    # Generate traffic on the LB so we can identify the current Master
    _validators.check_members_balanced(ip_address=ip_address,
                                       protocol=protocol,
                                       port=port,
                                       members_count=1,
                                       requests_count=1)

    # The amphora which has total_connections > 0 is the master.
    # Backup amphora will always have total_connections == 0.
    for amphora in amphorae:
        amphora_stats = _client.octavia_client(client).amphora_stats_show(
            amphora['id'])
        for listener in list(amphora_stats.values())[0]:
            if listener['total_connections'] > 0:
                return amphora

    raise ValueError("Master Amphora wasn't found!")
