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

import tobiko
from tobiko.openstack import keystone
from tobiko.shiftstack import _clouds_file


class ShiftstackKeystoneCredentialsFixture(
        keystone.CloudsFileKeystoneCredentialsFixture):

    clouds_file_fixture = tobiko.required_fixture(
        _clouds_file.ShiftStackCloudsFileFixture, setup=False)

    def __init__(self,
                 cloud_name: str = None,
                 clouds_file: str = None):
        if clouds_file is None:
            clouds_file = self.clouds_file_fixture.local_clouds_file_path
        if cloud_name is None:
            cloud_name = tobiko.tobiko_config().shiftstack.cloud_name
        super().__init__(clouds_file=clouds_file,
                         cloud_name=cloud_name)

    def setup_fixture(self):
        tobiko.setup_fixture(self.clouds_file_fixture)
        super().setup_fixture()


def shiftstack_keystone_session():
    return keystone.get_keystone_session(
        credentials=ShiftstackKeystoneCredentialsFixture)


def shiftstack_keystone_credentials():
    return tobiko.setup_fixture(
        ShiftstackKeystoneCredentialsFixture).credentials
