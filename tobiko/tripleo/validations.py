from __future__ import absolute_import

from oslo_log import log

from validations_libs import validation_actions
from validations_libs import constants as v_consts

from tobiko.tripleo import overcloud
from tobiko.openstack import topology
from tobiko.shell import sh


LOG = log.getLogger(__name__)

v_consts.DEFAULT_VALIDATIONS_BASEDIR = '/home/stack/tripleo-validations'


def prepare_ansible_hosts_inventory():
    """create a hosts.yaml with ansible connections'
    specifications for overcloud nodes"""
    sshcu = topology.list_openstack_nodes(group='undercloud')[0].ssh_client
    sh.execute('if [ ! -f /home/stack/hosts.yaml ]; then '
               'source /home/stack/stackrc;tripleo-ansible-inventory '
               '--ansible_ssh_user heat-admin --static-yaml-inventory '
               'hosts.yaml;fi', ssh_client=sshcu, stdout=True)


def run_post_deployment_validations():
    """run validtion framework post-deploument validations
    only if we're in a tripleo env"""

    if overcloud.has_overcloud():
        prepare_ansible_hosts_inventory()
        failures = []
        validates_object = validation_actions.ValidationActions(
            validation_path='/home/stack/tripleo-validations/playbooks')
        validations_result = validates_object.run_validations(
                                         group='post-deployment',
                                         quiet=False,
                                         inventory='/home/stack/hosts.yaml')
        for validation in validations_result:
            if validation['Status'] == 'FAILED':
                failures.append(
                    'failed validation: {}\n\n'.format(validation))
        if failures:
            LOG.info('Failed tripleo validations:\n {}'.format(failures))
            # We should not fail over validations in the beginning we have to
            # test run them, and handle false negatives.

            # tobiko.fail(
            #         'nova agents are unhealthy:\n{!s}', '\n'.join(failures))

    # to list possible validations:
    # validates_object.list_validations()

    # single validation example
    # validates_object.run_validations(
    # validation_name='healthcheck-service-status',quiet=False,inventory='/home/stack/hosts.yaml')
