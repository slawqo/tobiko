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

import time

from oslo_log import log

from tobiko import config
from tobiko.openstack import octavia
from tobiko.tests.scenario.octavia import exceptions

LOG = log.getLogger(__name__)

CONF = config.CONF


def wait_resource_operating_status(resource_type, operating_status,
                                   resource_get, *args):
    start = time.time()

    while time.time() - start < CONF.tobiko.octavia.check_timeout:
        res = resource_get(*args)
        if res['operating_status'] == operating_status:
            return

        time.sleep(CONF.tobiko.octavia.check_interval)

    raise exceptions.TimeoutException(
        reason=("Cannot get operating_status '{}' from {} {} "
                "within the timeout period.".format(operating_status,
                                                    resource_type, args)))


def wait_lb_operating_status(lb_id, operating_status):
    LOG.debug("Wait for loadbalancer {} to have '{}' "
              "operating_status".format(lb_id, operating_status))
    wait_resource_operating_status("loadbalancer",
                                   operating_status,
                                   octavia.get_loadbalancer,
                                   lb_id)


def wait_resource_provisioning_status(resource_type, provisioning_status,
                                      resource_get, *args):
    start = time.time()

    while time.time() - start < CONF.tobiko.octavia.check_timeout:
        res = resource_get(*args)
        if res['provisioning_status'] == provisioning_status:
            return

        time.sleep(CONF.tobiko.octavia.check_interval)

    raise exceptions.TimeoutException(
        reason=("Cannot get provisioning_status '{}' from {} {} "
                "within the timeout period.".format(provisioning_status,
                                                    resource_type, args)))


def wait_lb_provisioning_status(lb_id, provisioning_status):
    LOG.debug("Wait for loadbalancer {} to have '{}' "
              "provisioning_status".format(lb_id, provisioning_status))
    wait_resource_provisioning_status("loadbalancer",
                                      provisioning_status,
                                      octavia.get_loadbalancer,
                                      lb_id)


def wait_for_request_data(client_stack, server_ip_address,
                          server_protocol, server_port, request_function):
    """Wait until a request on a server succeeds

    Throws a TimeoutException after CONF.tobiko.octavia.check_timeout
    if the server doesn't reply.
    """
    start = time.time()

    while time.time() - start < CONF.tobiko.octavia.check_timeout:
        try:
            ret = request_function(client_stack, server_ip_address,
                                   server_protocol, server_port)
        except Exception as e:
            LOG.warning("Received exception {} while performing a "
                        "request".format(e))
        else:
            return ret
        time.sleep(CONF.tobiko.octavia.check_interval)

    raise exceptions.TimeoutException(
        reason=("Cannot get data from {} on port {} with "
                "protocol {} within the timeout period.".format(
                    server_ip_address, server_port, server_protocol)))


def wait_for_loadbalancer_is_active(loadbalancer_stack):
    loadbalancer_id = loadbalancer_stack.loadbalancer_id
    wait_lb_provisioning_status(loadbalancer_id, 'ACTIVE')


def wait_for_loadbalancer_functional(loadbalancer_stack, client_stack,
                                     loadbalancer_vip, loadbalancer_protocol,
                                     loadbalancer_port, request_function):
    """Wait until the load balancer is functional."""

    # Check load balancer status
    loadbalancer_id = loadbalancer_stack.loadbalancer_id
    wait_lb_operating_status(loadbalancer_id, 'ONLINE')

    wait_for_request_data(client_stack, loadbalancer_vip,
                          loadbalancer_protocol, loadbalancer_port,
                          request_function)


def wait_for_member_functional(client_stack, pool_stack, member_stack,
                               request_function):
    """Wait until a member server is functional."""

    member_ip = member_stack.server_stack.floating_ip_address
    member_port = member_stack.application_port
    member_protocol = pool_stack.pool_protocol

    wait_for_request_data(client_stack, member_ip, member_protocol,
                          member_port, request_function)
