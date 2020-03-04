from __future__ import absolute_import

import time

from oslo_log import log

import tobiko
from tobiko.openstack import nova

LOG = log.getLogger(__name__)


def check_nova_services_health(timeout=120, interval=2):
    failures = []
    start = time.time()

    while time.time() - start < timeout:
        failures = []
        nova_client = nova.get_nova_client()
        services = nova_client.services.list()

        for service in services:
            if not service.state == 'up':
                failures.append(
                    'failed service: {}\n\n'.format(vars(service)))
        if failures:
            LOG.info('Failed nova services:\n {}'.format(failures))
            LOG.info('Not all nova services are up ..')
            LOG.info('Retrying , timeout at: {}'
                     .format(timeout-(time.time() - start)))
            time.sleep(interval)
        else:
            LOG.info([vars(service) for service in services])
            LOG.info('All nova services are up!')
            return
    # exhausted all retries
    if failures:
        tobiko.fail(
            'nova agents are unhealthy:\n{!s}', '\n'.join(failures))


def start_all_instances():
    """try to start all stopped overcloud instances"""
    nova_client = nova.get_nova_client()
    servers = nova_client.servers.list()
    for instance in servers:
        nova.activate_server(instance)
