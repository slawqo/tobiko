from __future__ import absolute_import

import random
import time

from oslo_log import log
import pandas

import tobiko
from tobiko.shell import ping
from tobiko.openstack import nova
from tobiko.shell import sh
from tobiko.openstack import stacks


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


def stop_all_instances():
    """try to start all stopped overcloud instances"""
    for instance in nova.list_servers():
        activated_instance = nova.shutoff_server(instance)
        time.sleep(3)
        instance_info = 'instance {nova_instance} is {state} on {host}'.format(
            nova_instance=activated_instance.name,
            state=activated_instance.status,
            host=activated_instance._info[  # pylint: disable=W0212
                'OS-EXT-SRV-ATTR:hypervisor_hostname'])
        LOG.info(instance_info)
        if activated_instance.status != 'SHUTOFF':
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


def get_vms_table():
    """populate a dataframe with vm host,id,status"""
    vms_data = [(vm._info[  # pylint: disable=W0212
                     'OS-EXT-SRV-ATTR:hypervisor_hostname'], vm.id,
                 vm.status) for vm in nova.list_servers()]
    vms_df = pandas.DataFrame(vms_data, columns=['vm_host', 'vm_id',
                                                 'vm_state'])
    return vms_df


def list_computes():
    """list compute host names"""
    return [compute.hypervisor_hostname for compute in nova.list_hypervisors()]


def get_compute_vms_df(compute_host):
    """input: compute hostname (can be short)
    output: dataframe with vms of that host"""
    return get_vms_table().query(f"vm_host=='{compute_host}'")


def get_random_compute_with_vms_name():
    """get a randomcompute holding vm/s"""
    for compute in list_computes():
        if not get_compute_vms_df(compute).empty:
            return compute


def vm_info(vm_id, vms_df):
    """input: vm and a vms df
    output: host string"""
    return vms_df.query(f"vm_id == '{vm_id}'").to_string()


def vm_df(vm_id, vms_df):
    """input: vm and a vms df
    output: host string"""
    return vms_df.query(f"vm_id == '{vm_id}'")


def vm_floating_ip(vm_id):
    """input: vm_id
    output it's floating ip"""

    vm = nova.get_server(vm_id)
    floating_ip = nova.list_server_ip_addresses(
        vm, address_type='floating').first
    return floating_ip


def check_ping_vm_fip(fip):
    ping.ping_until_received(fip).assert_replied()


def check_df_vms_ping(df):
    """input: dataframe with vms_ids
    try to ping all vms in df"""
    for vm_id in df.vm_id.to_list():
        check_ping_vm_fip(vm_floating_ip(vm_id))


def vm_location(vm_id, vms_df):
    """input: vm and a vms df
    output: host string"""
    return vms_df.query(f"vm_id == '{vm_id}'")['vm_host'].to_string(
            index=False)


def check_vm_evacuations(vms_df_old=None, vms_df_new=None, timeout=120,
                         interval=2, check_no_evacuation=False):
    """check evacuation of vms
    input: old and new vms_state_tables dfs"""
    failures = []
    start = time.time()

    while time.time() - start < timeout:
        failures = []
        for vm_id in vms_df_old.vm_id.to_list():
            old_bm_host = vm_location(vm_id, vms_df_old)
            new_vm_host = vm_location(vm_id, vms_df_new)

            if check_no_evacuation:
                cond = bool(old_bm_host != new_vm_host)
            else:
                cond = bool(old_bm_host == new_vm_host)

            if cond:
                failures.append(
                    'failed vm evacuations: {}\n\n'.format(vm_info(vm_id,
                                                           vms_df_old)))
            if failures:
                LOG.info('Failed nova evacuation:\n {}'.format(failures))
                LOG.info('Not all nova vms evacuated ..')
                LOG.info('Retrying , timeout at: {}'
                         .format(timeout-(time.time() - start)))
                time.sleep(interval)
            else:
                LOG.info(vms_df_old.to_string())
                LOG.info('All vms were evacuated!')
                return
    # exhausted all retries
    if failures:
        tobiko.fail(
            'failed vm evacuations:\n{!s}', '\n'.join(failures))


# check vm create with ssh and ping checks
def random_vm_create(stack_name='stack{}'.format(
                    random.randint(0, 1000000)),
                    stack_template=stacks.CirrosServerStackFixture):
    """stack_name: unique stack name ,
    so that each time a new vm is created"""
    # create a vm
    LOG.info(f'creating vm - {stack_name}')
    stack = stack_template(
        stack_name=stack_name)
    tobiko.reset_fixture(stack)
    stack.wait_for_create_complete()
    tobiko.cleanup_fixture(stack.ssh_client)
    # Test SSH connectivity to floating IP address
    sh.get_hostname(ssh_client=stack.ssh_client)

    # Test ICMP connectivity to floating IP address
    ping.ping_until_received(
        stack.floating_ip_address).assert_replied()
    return stack


def random_vm_create_evacuable_image_tag():
    return random_vm_create(stack_template=stacks.EvacuableServerStackFixture)


def random_vm_create_shutoff_state():
    return nova.shutoff_server(random_vm_create().server_details)


def get_stack_server_id(stack):
    return stack.server_details.id


def create_multiple_unique_vms(n_vms=2):
    """create n_vms(int)"""
    for _ in range(n_vms):
        stack_name = 'stack{}'.format(random.randint(0, 1000000))
        random_vm_create(stack_name)
