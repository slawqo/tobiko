from __future__ import absolute_import

import time

from neutronclient.common import exceptions as neutron_exc
from oslo_log import log

import tobiko
from tobiko.openstack import neutron

LOG = log.getLogger(__name__)


def check_neutron_agents_health(timeout=60, interval=5):
    failures = []
    neutron_client = neutron.get_neutron_client()
    start = time.time()

    while time.time() - start < timeout:
        try:
            # get neutron agent list
            agents = neutron_client.list_agents()
        except neutron_exc.ServiceUnavailable:
            # retry in case neutron server was unavailable after disruption
            LOG.warning("neutron server was not available - retrying...")
            time.sleep(interval)
        else:
            LOG.info("neutron agents status retrieved")
            break

    for agent in agents['agents']:
        if not agent['alive']:
            failures.append('failed agent: {}\n\n'.format(agent))

    if failures:
        tobiko.fail(
            'neutron agents are unhealthy:\n{!s}', '\n'.join(failures))
    else:
        LOG.info('All neutron agents are healthy!')
