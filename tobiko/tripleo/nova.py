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
    for instance in nova.list_servers():
        activated_instance = nova.activate_server(instance)
        time.sleep(3)
        instance_info = 'instance {nova_instance} is {state} on {host}'.format(
            nova_instance=activated_instance.name,
            state=activated_instance.status,
            host=activated_instance._info[  # pylint: disable=W0212
                'OS-EXT-SRV-ATTR:hypervisor_hostname'])
        LOG.info(instance_info)
        if activated_instance.status != 'ACTIVE':
            tobiko.fail(instance_info)


def wait_for_all_instances_status(status, timeout=None):
    """wait for all instances for a certain status or raise an exception"""
    for instance in nova.list_servers():
        nova.wait_for_server_status(server=instance.id, status=status,
                                    timeout=timeout)
        instance_info = 'instance {nova_instance} is {state} on {host}'.format(
            nova_instance=instance.name,
            state=status,
            host=instance._info[  # pylint: disable=W0212
                'OS-EXT-SRV-ATTR:hypervisor_hostname'])
        LOG.info(instance_info)
