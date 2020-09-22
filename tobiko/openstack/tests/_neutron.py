from __future__ import absolute_import

import json

from oslo_log import log

import tobiko
from tobiko.openstack import neutron
from tobiko.shell import sh

LOG = log.getLogger(__name__)


def get_osp_version():
    from tobiko.tripleo import undercloud_ssh_client
    try:
        result = sh.execute("awk '{print $6}' /etc/rhosp-release",
                            ssh_client=undercloud_ssh_client())
    except (sh.ShellCommandFailed, sh.ShellTimeoutExpired):
        LOG.debug("File /etc/rhosp-release not found")
        return None
    else:
        return result.stdout.splitlines()[0]


def is_ovn_configured():
    from tobiko.tripleo import containers
    return containers.ovn_used_on_overcloud()


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

        rhosp_version = get_osp_version()
        rhosp_major_release = (int(rhosp_version.split('.')[0])
                               if rhosp_version
                               else None)

        if (rhosp_major_release and rhosp_major_release <= 13 and
                is_ovn_configured()):
            LOG.debug("Neutron list agents should return an empty list with"
                      "OVN and RHOSP releases 13 or earlier")
            test_case.assertEqual([], agents)
            return agents

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
