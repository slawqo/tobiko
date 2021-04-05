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

import collections

from tobiko import config


CONF = config.CONF


def get_iperf_parameters(mode, ip=None, **iperf_params):
    """Get iperf parameters
    mode allowed values: client or server
    ip is only needed for client mode
    """
    return IperfParameters(
        mode=mode,
        ip=ip,
        port=iperf_params.get('port', CONF.tobiko.iperf.port),
        timeout=iperf_params.get('timeout', CONF.tobiko.iperf.timeout),
        output_format=iperf_params.get('output_format',
                                       CONF.tobiko.iperf.output_format),
        download=iperf_params.get('download', CONF.tobiko.iperf.download),
        bitrate=iperf_params.get('bitrate', CONF.tobiko.iperf.bitrate),
        protocol=iperf_params.get('protocol', CONF.tobiko.iperf.protocol))


class IperfParameters(collections.namedtuple('IperfParameters',
                                             ['mode',
                                              'ip',
                                              'port',
                                              'timeout',
                                              'output_format',
                                              'download',
                                              'bitrate',
                                              'protocol'])):
    """Recollect parameters to be used to format iperf command line

    IperfParameters class is a data model recollecting parameters used to
    create an iperf command line. It provides the feature of copying default
    values from another instance of IperfParameters passed using constructor
    parameter 'default'.
    """
