# Copyright 2022 Red Hat
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

import typing

from oslo_log import log

import tobiko
from tobiko import tripleo
from tobiko import config
from tobiko.openstack.octavia import _client
from tobiko.openstack import nova, openstacksdkclient
from tobiko.openstack.octavia import _validators
from tobiko.openstack import topology
from tobiko.shell import sh

LOG = log.getLogger(__name__)
CONF = config.CONF

AmphoraType = typing.Dict[str, typing.Any]
AmphoraIdType = typing.Union[str, AmphoraType]


def get_os_conn():
    """Get openstacksdk client fixture
    """
    return openstacksdkclient.openstacksdk_client()


def get_amphora(amp_id: str):
    return get_os_conn().load_balancer.get_amphora(amp_id)


def list_amphorae(load_balancer_id: str = None, **params):
    if load_balancer_id is not None:
        params['load_balancer_id'] = load_balancer_id
    return get_os_conn().load_balancer.amphorae(
        loadbalancer_id=load_balancer_id)


def get_amphora_compute_node(load_balancer_id: str,
                             port: int,
                             protocol: str,
                             ip_address: str,
                             client: _client.OctaviaClientType = None) -> (
        topology.OpenStackTopologyNode):
    """Gets the compute node which hosts the LB amphora

    This function finds the Overcloud compute node which
    hosts the amphora. In case there are more than 1 amphora
    (e.g. if the LB's topology is Active/standby), so the compute node which
    hosts the master amphora will be returned.

    :param load_balancer_id: the load balancer ID.
    :param port: the load balancer port.
    :param protocol: the load balancer protocol.
    :param ip_address: the IP address of the load balancer
    :param client: the Octavia client
    :return: the compute node which hosts the Amphora.
    """
    amphorae = list_amphorae(load_balancer_id=load_balancer_id)
    amphora = get_master_amphora(amphorae=amphorae,
                                 port=port,
                                 protocol=protocol,
                                 ip_address=ip_address,
                                 client=client)
    server = nova.get_server(amphora['compute_id'])
    hostname = getattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname')
    return topology.get_openstack_node(hostname=hostname)


# TODO (oschwart): use openstacksdk in this method implementation whenever
#  openstacksdk has its API call
def get_amphora_stats(amphora_id, client=None):
    """
    :param amphora_id: the amphora id
    :param client: The Octavia client
    :return (dict): The amphora stats dict.
    """

    return _client.octavia_client(client).amphora_stats_show(amphora_id)


def get_master_amphora(amphorae: typing.Iterable[AmphoraType],
                       port: int,
                       protocol: str,
                       ip_address: str,
                       client=None) -> AmphoraType:
    """Gets the master Amphora in a High Available LB
    (a loadbalancer which uses the Active/standby topology)

    :param amphorae: The list of amphoras (each represented by
     JSON).
    :param port: the load balancer port.
    :param protocol: the load balancer protocol.
    :param ip_address: the IP address of the load balancer
    :param client: the Octavia client
    :return amphora (dict): JSON of the Master Amphora.
    """

    amphorae = tobiko.select(amphorae)
    try:
        return amphorae.unique
    except tobiko.MultipleObjectsFound:
        # For a high available LB
        pass

    # Generate traffic on the LB so we can identify the current Master
    _validators.check_members_balanced(ip_address=ip_address,
                                       protocol=protocol,
                                       port=port,
                                       members_count=1,
                                       requests_count=1)

    # The amphora which has total_connections > 0 is the master.
    # Backup amphora will always have total_connections == 0.
    for amphora in amphorae:
        amphora_stats = get_amphora_stats(amphora_id=amphora['id'],
                                          client=client)
        for listener in list(amphora_stats.values())[0]:
            if listener['total_connections'] > 0:
                LOG.debug(f"Chosen amphora is {amphora['id']} with the "
                          f"following stats: {amphora_stats}")
                return amphora

    raise ValueError("Master Amphora wasn't found!")


def run_command_on_amphora(command: str,
                           lb_id: str = None,
                           lb_vip: str = None,
                           amp_id: str = None,
                           sudo: bool = False) -> str:
    """
    Run a given command on the master/single amphora

    :param command: The command to run on the amphora
    :param lb_id: The load balancer id whose amphora should run the command
    :param lb_vip: The loadbalancer VIP
    :param amp_id: The single/master amphora id
    :param sudo: (bool) Whether to run the command with sudo permissions
           on the amphora
    :return: The command output (str)
    """
    # Get the master/single amphora lb_network_ip
    if amp_id:
        amp_lb_network_ip = get_amphora(amp_id)['lb_network_ip']
    elif lb_id and lb_vip:
        amphorae = list_amphorae(load_balancer_id=lb_id)
        amphora = get_master_amphora(amphorae=amphorae,
                                     port=80,
                                     protocol='HTTP',
                                     ip_address=lb_vip)
        amp_lb_network_ip = amphora['lb_network_ip']
    else:
        raise ValueError('Either amphora id or both the loadbalancer id '
                         'and the loadbalancer floating ip need to be '
                         'provided.')

    # Find the undercloud ssh client and (any) controller ip
    def _get_overcloud_node_ssh_client(group):
        return topology.list_openstack_nodes(group=group)[0].ssh_client

    controller_ip = _get_overcloud_node_ssh_client('controller').host
    undercloud_client = _get_overcloud_node_ssh_client('undercloud')

    if not controller_ip or not undercloud_client:
        raise RuntimeError(f'Either controller ip {controller_ip} or '
                           f'undercloud ssh client {undercloud_client} was'
                           ' not found.')

    # Preparing ssh command
    osp_major_version = tripleo.overcloud_version().major
    if osp_major_version == 16:
        ssh_add_command = 'ssh-add'
    elif osp_major_version == 17:
        ssh_add_command = 'sudo -E ssh-add /etc/octavia/ssh/octavia_id_rsa'
    else:
        raise NotImplementedError('The ssh_add_command is not implemented '
                                  f'for OSP version {osp_major_version}.')

    ssh_agent_output = sh.execute(
        'ssh-agent -s',
        ssh_client=undercloud_client).stdout.strip()
    # Example: eval {ssh_agent_output} ssh-add
    start_agent_cmd = f'eval {ssh_agent_output} {ssh_add_command}; '

    # Example: ssh -A -t heat-admin@192.168.24.13
    controller_user = tripleo.get_overcloud_ssh_username()
    controller_ssh_command = f'ssh -A -t {controller_user}@{controller_ip}'

    amphora_user = CONF.tobiko.octavia.amphora_user
    # Example: ssh -o StrictHostKeyChecking=no cloud-user@172.24.0.214
    amphora_ssh_command = 'ssh -o StrictHostKeyChecking=no ' \
                          f'{amphora_user}@{amp_lb_network_ip}'
    full_amp_ssh_cmd = f'{controller_ssh_command} {amphora_ssh_command}'
    if sudo:
        command = f'sudo {command}'

    # Example:
    # $(ssh-agent -s) > ssh_agent_output
    #
    # eval {ssh_agent_output}; ssh-add; ssh -A -t heat-admin@192.168.24.13\
    # ssh -o StrictHostKeyChecking=no cloud-user@172.24.0.214 <command>
    command = f'{start_agent_cmd} {full_amp_ssh_cmd} {command}'
    out = sh.execute(command,
                     ssh_client=undercloud_client,
                     sudo=False).stdout.strip()

    # Removing the ssh-agent output
    # 'Agent pid 642546\n<output-we-want>' -> '<output-we-want>'
    formatted_out = '\n'.join(out.split('\n')[1:])
    return formatted_out
