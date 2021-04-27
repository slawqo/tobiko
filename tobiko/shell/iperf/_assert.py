# Copyright (c) 2019 Red Hat, Inc.
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
from __future__ import division

from oslo_log import log

import tobiko
from tobiko import config
from tobiko.shell.iperf import _iperf


CONF = config.CONF
LOG = log.getLogger(__name__)


def calculate_bw(iperf_measures):
    # first interval is removed because BW measured during it is not
    # limited - it takes ~ 1 second to traffic shaping algorithm to apply
    # bw limit properly (buffer is empty when traffic starts being sent)
    intervals = iperf_measures['intervals'][1:]

    bits_received = sum([interval['sum']['bytes'] * 8
                         for interval in intervals])
    totaltime = sum([interval['sum']['seconds'] for interval in intervals])
    # bw in bits per second
    return bits_received / totaltime


def assert_bw_limit(ssh_client, ssh_server, **params):
    iperf_measures = _iperf.iperf(ssh_client, ssh_server, **params)
    measured_bw = calculate_bw(iperf_measures)

    testcase = tobiko.get_test_case()
    bw_limit = float(params.get('bw_limit') or
                     CONF.tobiko.neutron.bwlimit_kbps * 1000.)
    LOG.debug('measured_bw = %f', measured_bw)
    LOG.debug('bw_limit = %f', bw_limit)
    # a 5% of upper deviation is allowed
    testcase.assertLess(measured_bw, bw_limit * 1.1)
    # an 8% of lower deviation is allowed
    testcase.assertGreater(measured_bw, bw_limit * 0.9)
