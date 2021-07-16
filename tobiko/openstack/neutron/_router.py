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

import typing
import json

from oslo_log import log

import tobiko
from tobiko.openstack.neutron import _agent


LOG = log.getLogger(__name__)


def wait_for_master_and_backup_agents(
        router_id: str,
        unique_master: bool = True,
        timeout: tobiko.Seconds = None,
        interval: tobiko.Seconds = None) -> \
        typing.Tuple[typing.Dict, typing.List[typing.Dict]]:
    for attempt in tobiko.retry(timeout=timeout,
                                interval=interval,
                                default_timeout=300.,
                                default_interval=5.):
        router_agents = _agent.list_l3_agent_hosting_routers(router_id)
        master_agents = router_agents.with_items(ha_state='active')
        if master_agents:
            LOG.debug(
                f"Router '{router_id}' has {len(master_agents)} master "
                "agent(s):\n"
                f"{json.dumps(master_agents, indent=4, sort_keys=True)}")
        backup_agents = router_agents.with_items(ha_state='standby')
        if backup_agents:
            LOG.debug(
                f"Router '{router_id}' has {len(backup_agents)} backup "
                "agent(s)):\n"
                f"{json.dumps(backup_agents, indent=4, sort_keys=True)}")
        other_agents = [agent
                        for agent in router_agents
                        if (agent not in master_agents + backup_agents)]
        if other_agents:
            LOG.debug(
                f"Router '{router_id}' has {len(other_agents)} other "
                "agent(s):\n"
                f"{json.dumps(master_agents, indent=4, sort_keys=True)}")
        try:
            if unique_master:
                master_agent = master_agents.unique
            else:
                master_agent = master_agents.first
        except (tobiko.MultipleObjectsFound, tobiko.ObjectNotFound):
            attempt.check_limits()
        else:
            break
    else:
        raise RuntimeError("tobiko retry loop ended before break?")

    return master_agent, backup_agents
