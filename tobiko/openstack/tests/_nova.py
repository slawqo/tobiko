# Copyright (c) 2020 Red Hat, Inc.
#
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

import os
import typing  # noqa

# import testtools

import tobiko
from tobiko.shell import ping
from tobiko.shell import sh
from tobiko.openstack import nova
from tobiko.openstack.stacks import _cirros
from tobiko.openstack.stacks import _nova


class TestServerCreationStack(_cirros.CirrosServerStackFixture):
    """Nova instance intended to be used for testing server creation"""


def test_server_creation(stack=TestServerCreationStack):
    """Test Nova server creation
    """
    return test_servers_creation(stack=stack,
                                 number_of_servers=0).first


class TestEvacuableServerCreationStack(_cirros.EvacuableServerStackFixture):
    """Nova instance intended to be used for testing server creation"""


def test_evacuable_server_creation():
    """Test evacuable Nova server creation
    """
    return test_server_creation(stack=TestEvacuableServerCreationStack)


def test_server_creation_and_shutoff(stack=TestServerCreationStack):
    result = test_server_creation(stack=stack)
    nova.shutoff_server(result.server_details)
    return result


def test_servers_creation(stack=TestServerCreationStack,
                          number_of_servers=2) -> \
        typing.List[_nova.ServerStackFixture]:
    pid = os.getpid()
    fixture_obj = tobiko.get_fixture_class(stack)

    # Get list of server stack instances
    fixtures = tobiko.Selection(
        tobiko.get_fixture(fixture_obj, fixture_id=f'{pid}-{i}')
        for i in range(number_of_servers or 1))

    testcase = tobiko.get_test_case()

    # Check fixtures types
    for fixture in fixtures:
        testcase.assertIsInstance(fixture, _nova.ServerStackFixture)

    # Delete all servers stacks
    for fixture in fixtures:
        tobiko.cleanup_fixture(fixture)

    # Create all servers stacks
    for fixture in fixtures:
        testcase.useFixture(fixture)

    # Test SSH connectivity to floating IP address
    testcase.assertEqual(
        {fixture.server_id: fixture.server_name
         for fixture in fixtures},
        {fixture.server_id: sh.get_hostname(ssh_client=fixture.ssh_client)
         for fixture in fixtures})

    # Test pinging to floating IP address
    ping.assert_reachable_hosts(fixture.floating_ip_address
                                for fixture in fixtures)
    return fixtures
