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

from collections import abc
import typing

from tobiko.openstack.designate import _client

DesignateZone = typing.Mapping[str, typing.Any]
DesignateZoneType = typing.Union[str, typing.Mapping[str, typing.Any]]


def designate_zone_id(zone: DesignateZoneType) -> str:
    if isinstance(zone, str):
        return zone
    elif isinstance(zone, abc.Mapping):
        return zone['id']
    else:
        raise TypeError(f'{zone} object is an invalid Designate zone type')


def get_designate_zone(zone: str,
                       client: _client.DesignateClientType = None) \
        -> DesignateZone:
    zone_id = designate_zone_id(zone)
    return _client.designate_client(client).zones.get(zone_id)
