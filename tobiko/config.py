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
from oslo_config import cfg

from tempest import config


CONF = config.CONF


TobikoGroup = [
    cfg.StrOpt('floating_network_name',
               default='public',
               help="Floating network name "),
    cfg.StrOpt('admin_username',
               help="Username to use for admin API requests."),
]

tobiko_group = cfg.OptGroup(name="tobiko_plugin",
                            title="Tobiko Plugin Options")
