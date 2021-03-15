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
