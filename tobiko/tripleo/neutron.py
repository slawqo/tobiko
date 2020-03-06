from __future__ import absolute_import

from oslo_log import log

import tobiko
from tobiko.openstack import neutron

LOG = log.getLogger(__name__)


def check_neutron_agents_health():
    failures = []
    neutron_client = neutron.get_neutron_client()
    agents = neutron_client.list_agents()

    for agent in agents['agents']:
        if not agent['alive']:
            failures.append('failed agent: {}\n\n'.format(agent))

    if failures:
        tobiko.fail(
            'neutron agents are unhealthy:\n{!s}', '\n'.join(failures))
    else:
        LOG.info('All neutron agents are healthy!')
