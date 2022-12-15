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

from tobiko.openstack.octavia import _amphora
from tobiko.openstack.octavia import _client
from tobiko.openstack.octavia import _constants
from tobiko.openstack.octavia import _exceptions
from tobiko.openstack.octavia import _load_balancer
from tobiko.openstack.octavia import _validators
from tobiko.openstack.octavia import _waiters

AmphoraIdType = _amphora.AmphoraIdType
AmphoraType = _amphora.AmphoraType
get_amphora_id = _amphora.get_amphora_id
get_amphora = _amphora.get_amphora
get_amphora_compute_node = _amphora.get_amphora_compute_node
get_master_amphora = _amphora.get_master_amphora
list_amphorae = _amphora.list_amphorae
get_amphora_stats = _amphora.get_amphora_stats
run_command_on_amphora = _amphora.run_command_on_amphora

OCTAVIA_CLIENT_CLASSSES = _client.OCTAVIA_CLIENT_CLASSSES
get_octavia_client = _client.get_octavia_client
octavia_client = _client.octavia_client
OctaviaClientFixture = _client.OctaviaClientFixture
OctaviaClientType = _client.OctaviaClientType
get_member = _client.get_member
list_members = _client.list_members

LoadBalancerIdType = _load_balancer.LoadBalancerIdType
LoadBalancerType = _load_balancer.LoadBalancerType
get_load_balancer = _load_balancer.get_load_balancer
get_load_balancer_id = _load_balancer.get_load_balancer_id

# Waiters
wait_for_status = _waiters.wait_for_status

# Validators
check_members_balanced = _validators.check_members_balanced

# Exceptions
RequestException = _exceptions.RequestException
TimeoutException = _exceptions.TimeoutException
OctaviaClientException = _exceptions.OctaviaClientException
RoundRobinException = _exceptions.RoundRobinException
TrafficTimeoutError = _exceptions.TrafficTimeoutError
AmphoraMgmtPortNotFound = _exceptions.AmphoraMgmtPortNotFound

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
