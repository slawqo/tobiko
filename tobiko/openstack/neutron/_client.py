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

from neutronclient.v2_0 import client as neutronclient

from tobiko.openstack import _client
from tobiko.openstack.neutron import _exceptions


class NeutronClientFixture(_client.OpenstackClientFixture):

    def init_client(self, session):
        return neutronclient.Client(session=session)


CLIENTS = _client.OpenstackClientManager(init_client=NeutronClientFixture)


def get_neutron_client(session=None, shared=True, init_client=None,
                       manager=None):
    manager = manager or CLIENTS
    client = manager.get_client(session=session, shared=shared,
                                init_client=init_client)
    client.setUp()
    return client.client


def find_network(network, session=None, **params):
    networks = [n
               for n in list_network(session=session, **params)
               if network in (n['name'], n['id'])]

    if not networks:
        raise _exceptions.NoSuchNetwork(network=network)

    elif len(networks) > 1:
        network_ids = [n['id'] for n in networks]
        raise _exceptions.MoreNetworksFound(
            network=network,
            netowrk_ids=(', '.join(network_ids)))

    return networks[0]


def list_network(session=None, **params):
    return get_neutron_client(session=session).list_networks(**params)[
        'networks']


def show_network(network, session=None, **params):
    return get_neutron_client(session=session).show_network(
        network, **params)['network']


def show_router(router, session=None, **params):
    return get_neutron_client(session=session).show_router(
        router, **params)['router']


def show_subnet(subnet, session=None, **params):
    return get_neutron_client(session=session).show_subnet(
        subnet, **params)['subnet']
