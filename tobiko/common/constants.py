# Copyright 2018 Red Hat
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

from tobiko import config

COMPLETE_STATUS = "CREATE_COMPLETE"
TEMPLATE_SUFFIX = ".yaml"

DEFAULT_PARAMS = {
    'public_net': config.get_any_option(
        'tobiko.network.floating_network_name',
        'tempest.network.floating_network_name'),
    'image': config.get_any_option(
        'tobiko.compute.image_ref',
        'tempest.compute.image_ref'),
    'flavor': config.get_any_option(
        'tobiko.compute.flavor_ref',
        'tempest.compute.flavor_ref'),
}
