# Copyright (c) 2021 Red Hat, Inc.
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

import dpkt
from oslo_log import log

import tobiko


LOG = log.getLogger(__name__)


def assert_pcap_content(pcap: dpkt.pcap.Reader, expect_empty: bool):
    actual_empty = True
    for _ in pcap:
        actual_empty = False
        break
    testcase = tobiko.get_test_case()
    LOG.debug(f'Is the obtained pcap file empty? {actual_empty}')
    testcase.assertEqual(expect_empty, actual_empty)


def assert_pcap_is_empty(pcap: dpkt.pcap.Reader):
    LOG.debug('This test expects an empty pcap capture')
    assert_pcap_content(pcap, True)


def assert_pcap_is_not_empty(pcap: dpkt.pcap.Reader):
    LOG.debug('This test expects a non-empty pcap capture')
    assert_pcap_content(pcap, False)
