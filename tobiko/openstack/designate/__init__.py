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

from tobiko.openstack.designate import _client
from tobiko.openstack.designate import _constants

DesignateClientFixture = _client.DesignateClientFixture
designate_client = _client.designate_client
get_designate_client = _client.get_designate_client
DESIGNATE_CLIENT_CLASSES = _client.DESIGNATE_CLIENT_CLASSES

designate_zone_id = _client.designate_zone_id
get_designate_zone = _client.get_designate_zone
list_recordsets = _client.list_recordsets
create_recordsets = _client.create_recordsets
get_recordset = _client.get_recordset

# Waiters
wait_for_status = _client.wait_for_status

# Constants
STATUS = _constants.STATUS
ACTIVE = _constants.ACTIVE
ERROR = _constants.ERROR
