# Copyright (c) 2022 Red Hat, Inc.
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

import typing

from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack import heat
from tobiko.openstack import designate
from tobiko.openstack.stacks import _hot

CONF = config.CONF
LOG = log.getLogger(__name__)


class DesignateZoneStackFixture(heat.HeatStackFixture):
    template = _hot.heat_template_file('designate/zone.yaml')

    record_name = 'record'

    record_type = 'A'

    recordset_records = ['192.10.1.1']

    @property
    def zone_name(self) -> str:
        return tobiko.get_fixture_name(self).lower() + '.'

    @property
    def zone_details(self) -> typing.Mapping[str, typing.Any]:
        return designate.get_designate_zone(self.zone_id)

    @property
    def recordset_list(self) -> typing.Mapping[str, typing.Any]:
        return designate.list_recordsets(self.zone_id)

    def recordset_create(self):
        return designate.create_recordsets(
            self.zone_id,
            name=self.record_name,
            type_=self.record_type,
            records=self.recordset_records)

    def wait_for_active_recordsets(self):
        for recordset in designate.list_recordsets(self.zone_id):
            self.wait_for_active_recordset(zone_id=self.zone_id,
                                           recordset_id=recordset['id'])

    def wait_for_active_recordset(self, zone_id, recordset_id, **kwargs):
        designate.wait_for_status(
            status_key=designate.STATUS,
            status=designate.ACTIVE,
            get_client=designate.get_recordset,
            object_id=zone_id,
            recordset_id=recordset_id, **kwargs
        )
