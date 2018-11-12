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
from tempest import config

conf = config.CONF

COMPLETE_STATUS = "CREATE_COMPLETE"
DEFAULT_FLAVOR = "m1.micro"

DEFAULT_API_VER = 2

TEMPLATE_SUFFIX = ".yaml"

DEFAULT_PARAMS = {
    'public_net': conf.network.floating_network_name,
    'image': conf.compute.image_ref,
    'flavor': DEFAULT_FLAVOR
}
