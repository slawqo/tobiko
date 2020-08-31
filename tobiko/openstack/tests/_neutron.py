from __future__ import absolute_import

import json

from oslo_log import log

import tobiko
from tobiko.openstack import neutron

LOG = log.getLogger(__name__)


def test_neutron_agents_are_alive(timeout=300., interval=5.):
    test_case = tobiko.get_test_case()
    for attempt in tobiko.retry(timeout=timeout, interval=interval):
        LOG.debug("Look for unhealthy Neutron agents...")
        try:
            # get Neutron agent list
            agents = neutron.list_agents()
        except neutron.ServiceUnavailable as ex:
            attempt.check_limits()
            # retry because Neutron server could still be unavailable after
            # a disruption
            LOG.debug(f"Waiting for neutron service... ({ex})")
            continue  # Let retry

        if not agents:
            test_case.fail("Neutron has no agents")

        dead_agents = agents.with_items(alive=False)
        if dead_agents:
            dead_agents_details = json.dumps(agents, indent=4, sort_keys=True)
            try:
                test_case.fail("Unhealthy agent(s) found:\n"
                               f"{dead_agents_details}\n")
            except tobiko.FailureException:
                attempt.check_limits()
                # retry because some Neutron agent could still be unavailable
                # after a disruption
                LOG.debug("Waiting for Neutron agents to get alive...\n"
                          f"{dead_agents_details}")
                continue

        LOG.debug(f"All {len(agents)} Neutron agents are alive.")
        return agents
