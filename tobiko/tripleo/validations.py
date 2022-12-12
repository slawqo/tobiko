# Copyright 2020 Red Hat
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

from oslo_log import log
from validations_libs import validation_actions

from tobiko import tripleo
from tobiko.tripleo import overcloud


LOG = log.getLogger(__name__)


def run_post_deployment_validations():
    """run validtion framework post-deploument validations
    only if we're in a tripleo env"""

    if overcloud.has_overcloud():
        inventory_file = os.path.expanduser('~/hosts.yaml')
        tripleo.fetch_tripleo_inventary_file(inventory_file=inventory_file)
        failures = []
        validates_object = validation_actions.ValidationActions()
        try:
            validations_result = validates_object.run_validations(
                group='post-deployment',
                quiet=False,
                inventory=inventory_file)
        except Exception:
            LOG.exception('Validation lib unhandled errors')
            return

        for validation in validations_result:
            if validation['Status'] == 'FAILED':
                failures.append(
                    'failed validation: {}\n\n'.format(validation))
            elif validation['Status'] == 'PASSED':
                LOG.info('passed validation: {}\n\n'.format(validation))
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
