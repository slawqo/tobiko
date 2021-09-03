# Copyright (c) 2021 Red Hat
# All Rights Reserved.
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

# Octavia attributes
PROVISIONING_STATUS = 'provisioning_status'

# Octavia provisioning status
ACTIVE = 'ACTIVE'
ERROR = 'ERROR'
PENDING_UPDATE = 'PENDING_UPDATE'

# Octavia services
WORKER_SERVICE = 'tripleo_octavia_worker.service'
HOUSEKEEPING_SERVICE = 'tripleo_octavia_housekeeping.service'
HM_SERVICE = 'tripleo_octavia_health_manager.service'
API_SERVICE = 'tripleo_octavia_api.service'

# Octavia containers
WORKER_CONTAINER = 'octavia_worker'
HOUSEKEEPING_CONTAINER = 'octavia_housekeeping'
HM_CONTAINER = 'octavia_health_manager'
API_CONTAINER = 'octavia_api'
