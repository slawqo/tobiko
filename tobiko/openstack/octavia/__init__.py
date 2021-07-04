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

from tobiko.openstack.octavia import _client
from tobiko.openstack.octavia import _waiters
from tobiko.openstack.octavia import _constants
from tobiko.openstack.octavia import _validators
from tobiko.openstack.octavia import _exceptions


OCTAVIA_CLIENT_CLASSSES = _client.OCTAVIA_CLIENT_CLASSSES
get_octavia_client = _client.get_octavia_client
octavia_client = _client.octavia_client
OctaviaClientFixture = _client.OctaviaClientFixture
get_loadbalancer = _client.get_loadbalancer
get_member = _client.get_member
list_amphorae = _client.list_amphorae
get_amphora_vm = _client.get_amphora_vm
list_amphoras_compute_nodes = _client.list_amphoras_compute_nodes
get_amphoras_compute_nodes = _client.get_amphoras_compute_nodes

# Waiters
wait_for_status = _waiters.wait_for_status
wait_for_active_members_and_lb = _waiters.wait_for_active_members_and_lb
wait_for_lb_to_be_updated_and_active = (
        _waiters.wait_for_lb_to_be_updated_and_active)

# Validators
check_members_balanced = _validators.check_members_balanced

# Exceptions
RequestException = _exceptions.RequestException
TimeoutException = _exceptions.TimeoutException

# Constants
PROVISIONING_STATUS = _constants.PROVISIONING_STATUS
ACTIVE = _constants.ACTIVE
ERROR = _constants.ERROR
PENDING_UPDATE = _constants.PENDING_UPDATE
WORKER_SERVICE = _constants.WORKER_SERVICE
HOUSEKEEPING_SERVICE = _constants.HOUSEKEEPING_SERVICE
HM_SERVICE = _constants.HM_SERVICE
API_SERVICE = _constants.API_SERVICE
WORKER_CONTAINER = _constants.WORKER_CONTAINER
HOUSEKEEPING_CONTAINER = _constants.HOUSEKEEPING_CONTAINER
HM_CONTAINER = _constants.HM_CONTAINER
API_CONTAINER = _constants.API_CONTAINER
OCTAVIA_SERVICES = [WORKER_SERVICE, HOUSEKEEPING_SERVICE, HM_SERVICE,
                    API_SERVICE]
OCTAVIA_CONTAINERS = [WORKER_CONTAINER, HOUSEKEEPING_CONTAINER, HM_CONTAINER,
                      API_CONTAINER]
