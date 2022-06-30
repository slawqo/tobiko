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

import tobiko
from tobiko.openstack import heat
from tobiko.shiftstack import _keystone


def shiftstack_heat_client(obj: heat.HeatClientType) -> heat.HeatClient:
    if obj is None:
        return get_shiftstack_heat_client()
    else:
        return tobiko.check_valid_type(obj, heat.HeatClient)


def get_shiftstack_heat_client() -> heat.HeatClient:
    session = _keystone.shiftstack_keystone_session()
    return heat.get_heat_client(session=session)
