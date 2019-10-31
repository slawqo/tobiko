# Copyright (c) 2019 Red Hat, Inc.
#
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
from __future__ import absolute_import

from oslo_log import log

import tobiko
from tobiko.shell.ping import _ping


LOG = log.getLogger(__name__)


def assert_reachable_hosts(hosts, **params):
    unreachable_hosts = _ping.list_unreachable_hosts(hosts, **params)
    if unreachable_hosts:
        tobiko.fail("Unable to reach host(s): {!r}", unreachable_hosts)


def assert_unreachable_hosts(hosts, **params):
    reachable_hosts = _ping.list_reachable_hosts(hosts, **params)
    if reachable_hosts:
        tobiko.fail("Reached host(s): {!r}", reachable_hosts)
