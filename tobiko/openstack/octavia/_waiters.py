# Copyright (c) 2021 Red Hat
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
from tobiko.openstack import octavia
from tobiko import config
from tobiko.shell import sh

LOG = log.getLogger(__name__)

CONF = config.CONF


def wait_for_status(status_key, status, get_client, object_id,
                    interval: tobiko.Seconds = None,
                    timeout: tobiko.Seconds = None,
                    error_ok=False, **kwargs):
    """Waits for an object to reach a specific status.

    :param status_key: The key of the status field in the response.
                       Ex. provisioning_status
    :param status: The status to wait for. Ex. "ACTIVE"
    :param get_client: The tobiko client get method.
                        Ex. _client.get_loadbalancer
    :param object_id: The id of the object to query.
    :param interval: How often to check the status, in seconds.
    :param timeout: The maximum time, in seconds, to check the status.
    :param error_ok: When true, ERROR status will not raise an exception.
    :raises TimeoutException: The object did not achieve the status or ERROR in
                              the check_timeout period.
    :raises UnexpectedStatusException: The request returned an unexpected
                                       response code.
    """

    for attempt in tobiko.retry(timeout=timeout,
                                interval=interval,
                                default_timeout=(
                                        CONF.tobiko.octavia.check_timeout),
                                default_interval=(
                                        CONF.tobiko.octavia.check_interval)):
        response = get_client(object_id, **kwargs)
        if response[status_key] == status:
            return response

        if response[status_key] == octavia.ERROR and not error_ok:
            message = ('{name} {field} was updated to an invalid state of '
                       'ERROR'.format(name=get_client.__name__,
                                      field=status_key))
            raise octavia.RequestException(message)
        # it will raise tobiko.RetryTimeLimitError in case of timeout
        attempt.check_limits()

        LOG.debug(f"Waiting for {get_client.__name__} {status_key} to get "
                  f"from '{response[status_key]}' to '{status}'...")


def wait_for_members_to_be_reachable(members,
                                     lb_protocol: str,
                                     lb_port: int,
                                     interval: tobiko.Seconds = None,
                                     timeout: tobiko.Seconds = None,
                                     count: int = 10):

    # Wait for members to be reachable from localhost
    last_reached_id = 0
    for attempt in tobiko.retry(timeout=timeout,
                                count=count,
                                interval=interval):
        try:
            for member in members[last_reached_id:]:
                octavia.check_members_balanced(
                    members_count=1,
                    ip_address=member.server_stack.ip_address,
                    protocol=lb_protocol,
                    port=lb_port,
                    requests_count=1)
                last_reached_id += 1  # prevent retrying same member again
        except sh.ShellCommandFailed:
            LOG.info("Waiting for members to have HTTP service available...")
        else:
            break

        if attempt.is_last:
            break
    else:
        raise RuntimeError("Members couldn't be reached!")


def wait_for_active_and_functional_members_and_lb(
        members,
        pool_id: str,
        lb_protocol: str,
        lb_port: int,
        loadbalancer_id: str,
        interval: tobiko.Seconds = None,
        timeout: tobiko.Seconds = None):

    # Wait for members to have an ACTIVE provisioning status
    for member_stack in members:
        octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                                status=octavia.ACTIVE,
                                get_client=octavia.get_member,
                                object_id=pool_id,
                                member_id=member_stack.member_id)

    # Wait for LB to have an ACTIVE provisioning status
    octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                            status=octavia.ACTIVE,
                            get_client=octavia.get_loadbalancer,
                            object_id=loadbalancer_id)

    wait_for_members_to_be_reachable(members=members,
                                     lb_protocol=lb_protocol,
                                     lb_port=lb_port,
                                     timeout=timeout,
                                     interval=interval)


def wait_for_lb_to_be_updated_and_active(loadbalancer_id):
    octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                            status=octavia.PENDING_UPDATE,
                            get_client=octavia.get_loadbalancer,
                            object_id=loadbalancer_id)

    octavia.wait_for_status(status_key=octavia.PROVISIONING_STATUS,
                            status=octavia.ACTIVE,
                            get_client=octavia.get_loadbalancer,
                            object_id=loadbalancer_id)


def wait_for_octavia_service(loadbalancer_id: str,
                             interval: tobiko.Seconds = None,
                             timeout: tobiko.Seconds = None,
                             client=None):
    for attempt in tobiko.retry(timeout=timeout,
                                interval=interval,
                                default_timeout=180.,
                                default_interval=5.):
        try:
            octavia.list_amphorae(loadbalancer_id=loadbalancer_id,
                                  client=client)
        except octavia.OctaviaClientException as ex:
            LOG.debug(f"Error listing amphorae: {ex}")
            if attempt.is_last:
                raise
            LOG.info('Waiting for the LB to become functional again...')
        else:
            LOG.info('Octavia service is available!')
            break
