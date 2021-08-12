# Copyright 2021 Red Hat
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

import ast
import datetime
import re
import typing

import tobiko
from tobiko.openstack import neutron
from tobiko.openstack.topology import _topology
from tobiko.shell import files


class NeutronNovaResponse(typing.NamedTuple):
    hostname: str
    timestamp: float
    name: str
    server_uuid: str
    status: str
    code: int
    tag: str
    line: str

    def __lt__(self, other):
        return self.timestamp < other.timestamp


class NeutronNovaResponseReader(tobiko.SharedFixture):
    log_digger: files.MultihostLogFileDigger
    groups = ['controller']
    message_pattern = r'Nova event response: '
    datetime_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} [0-9:.]+) .+')
    service_name = neutron.SERVER
    responses: tobiko.Selection[NeutronNovaResponse]

    def setup_fixture(self):
        self.log_digger = self.useFixture(
            _topology.get_log_file_digger(
                service_name=self.service_name,
                groups=self.groups,
                pattern=self.message_pattern))
        self.read_responses()

    def _get_log_timestamp(self,
                           log: str) -> float:
        found = self.datetime_pattern.match(log)
        if not found:
            return 0.0
        return datetime.datetime.strptime(
            found.group(1), "%Y-%m-%d %H:%M:%S.%f").timestamp()

    def read_responses(self) \
            -> tobiko.Selection[NeutronNovaResponse]:
        responses = tobiko.Selection[NeutronNovaResponse]()
        message_pattern = re.compile(self.message_pattern)
        for hostname, line in self.log_digger.find_lines(
                new_lines=hasattr(self, 'responses')):
            found = message_pattern.search(line)
            assert found is not None
            response_text = line[found.end():].strip()
            response_data = ast.literal_eval(response_text)
            assert isinstance(response_data, dict)
            response = NeutronNovaResponse(
                hostname=hostname,
                line=line,
                timestamp=self._get_log_timestamp(line[:found.start()]),
                **response_data)
            responses.append(response)
        responses.sort()
        if hasattr(self, 'responses'):
            self.responses.extend(responses)
        else:
            self.responses = responses
        return responses


def read_neutron_nova_responses(
        reader: NeutronNovaResponseReader = None,
        new_lines=True,
        **attributes) \
        -> tobiko.Selection[NeutronNovaResponse]:
    if reader is None:
        reader = tobiko.setup_fixture(NeutronNovaResponseReader)
    responses = reader.read_responses()
    if not new_lines:
        responses = reader.responses
    if attributes and responses:
        responses = responses.with_attributes(**attributes)
    return responses
