from __future__ import absolute_import

import tobiko
from tobiko.openstack import nova


def check_nova_services_health():
    failures = []
    nova_client = nova.get_nova_client()
    services = nova_client.services.list()

    for service in services:
        if not service.state == 'up':
            failures.append('failed service: {}\n\n'.format(vars(service)))

    if failures:
        tobiko.fail(
            'nova agents are unhealthy:\n{!s}', '\n'.join(failures))
