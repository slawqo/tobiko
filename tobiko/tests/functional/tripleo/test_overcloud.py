# Copyright 2019 Red Hat
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

import netaddr
import pandas as pd
import six
import testtools

from tobiko import config
from tobiko.openstack import nova
from tobiko.tripleo import overcloud
from tobiko.tripleo import pacemaker
from tobiko.tripleo import services
from tobiko.tripleo import processes
from tobiko.tripleo import neutron
import tobiko

CONF = config.CONF


@overcloud.skip_if_missing_overcloud
class OvercloudSshConnectionTest(testtools.TestCase):

    def test_fetch_overcloud_credentials(self):
        env = overcloud.load_overcloud_rcfile()
        self.assertTrue(env['OS_AUTH_URL'])
        self.assertTrue(env.get('OS_USERNAME') or env.get('OS_USER_ID'))
        self.assertTrue(env['OS_PASSWORD'])
        self.assertTrue(env.get('OS_TENANT_NAME') or
                        env.get('OS_PROJECT_NAME') or
                        env.get('OS_TENANT_ID') or
                        env.get('OS_PROJECT_ID'))


@overcloud.skip_if_missing_overcloud
class OvercloudNovaApiTest(testtools.TestCase):

    def test_list_overcloud_nodes(self):
        nodes = overcloud.list_overcloud_nodes()
        self.assertTrue(nodes)
        for node in nodes:
            node_ip = nova.find_server_ip_address(server=node,
                                                  check_connectivity=True)
            self.assertIsInstance(node_ip, netaddr.IPAddress)

    def test_find_overcloud_nodes(self):
        node = overcloud.find_overcloud_node()
        node_ip = nova.find_server_ip_address(server=node,
                                              check_connectivity=True)
        self.assertIsInstance(node_ip, netaddr.IPAddress)

    def test_get_overcloud_node_ip_address(self):
        overcloud_node_ip = overcloud.overcloud_node_ip_address()
        self.assertIsInstance(overcloud_node_ip, netaddr.IPAddress)

    def test_overcloud_host_config(self):
        hostname = overcloud.find_overcloud_node().name
        host_config = tobiko.setup_fixture(
            overcloud.overcloud_host_config(hostname=hostname))
        self.assertEqual(hostname, host_config.host)
        self.assertIsInstance(host_config.hostname, six.string_types)
        netaddr.IPAddress(host_config.hostname)
        self.assertEqual(CONF.tobiko.tripleo.overcloud_ssh_port,
                         host_config.port)
        self.assertEqual(CONF.tobiko.tripleo.overcloud_ssh_username,
                         host_config.username)
        key_filename = os.path.expanduser(
            CONF.tobiko.tripleo.overcloud_ssh_key_filename)
        self.assertEqual(key_filename, host_config.key_filename)
        self.assertTrue(os.path.isfile(key_filename))
        self.assertTrue(os.path.isfile(key_filename + '.pub'))

    def test_overcloud_ssh_client_connection(self):
        hostname = overcloud.find_overcloud_node().name
        ssh_client = overcloud.overcloud_ssh_client(hostname=hostname)
        ssh_client.connect()


@overcloud.skip_if_missing_overcloud
class OvercloudPacemakerTest(testtools.TestCase):
    """
    Assert that all pacemaker resources are in
    healthy state
    """

    def test_get_pacemaker_resource_table(self):
        resource_table = pacemaker.get_pcs_resources_table()
        self.assertIsInstance(resource_table, pd.DataFrame)

    def test_pacemaker_resources_health(self):
        pcs_health = pacemaker.PacemakerResourcesStatus()
        self.assertTrue(pcs_health.all_healthy)


@overcloud.skip_if_missing_overcloud
class OvercloudServicesTest(testtools.TestCase):
    """
    Assert that a subset of overcloud services are in running state
    across the overcloud nodes
    """

    def test_get_services_resource_table(self):
        oss = services.OvercloudServicesStatus()
        self.assertIsInstance(oss.oc_services_df,
                              pd.DataFrame)

    def test_overcloud_services(self):
        oss = services.OvercloudServicesStatus()
        self.assertTrue(oss.basic_overcloud_services_running)

    def test_get_overcloud_nodes_running_pcs_resource(self):
        nodes_list = pacemaker.get_overcloud_nodes_running_pcs_resource(
            resource_type='(ocf::heartbeat:rabbitmq-cluster):',
            resource_state='Started')
        self.assertIsInstance(nodes_list, list)


@overcloud.skip_if_missing_overcloud
class OvercloudProcessesTest(testtools.TestCase):
    """
    Assert that a subset of overcloud processes are in running state
    across the overcloud nodes
    """

    def test_get_processes_resource_table(self):
        ops = processes.OvercloudProcessesStatus()
        self.assertIsInstance(ops.oc_procs_df,
                              pd.DataFrame)

    def test_overcloud_processes(self):
        ops = processes.OvercloudProcessesStatus()
        self.assertTrue(ops.basic_overcloud_processes_running)


@overcloud.skip_if_missing_overcloud
class OvercloudNeutronAgentsTest(testtools.TestCase):
    """
    Assert that a the neutron agents are healthy
    across the overcloud nodes
    """

    def test_neutron_agents_health(self):
        neutron.check_neutron_agents_health()
