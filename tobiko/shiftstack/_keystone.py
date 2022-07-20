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

import tobiko
from tobiko.openstack import keystone
from tobiko import tripleo


def load_shiftstack_rcfile() -> typing.Dict[str, str]:
    conf = tobiko.tobiko_config().shiftstack
    return tripleo.fetch_os_env(*conf.rcfile)


class ShiftstackKeystoneCredentialsFixture(
        tripleo.UndercloudCloudsFileKeystoneCredentialsFixture):

    @staticmethod
    def _get_default_cloud_name() -> typing.Optional[str]:
        return tobiko.tobiko_config().shiftstack.cloud_name

    def _get_environ(self) -> typing.Dict[str, str]:
        return load_shiftstack_rcfile()


def shiftstack_keystone_session() -> keystone.KeystoneSession:
    credentials = shiftstack_keystone_credentials()
    return keystone.get_keystone_session(credentials=credentials)


def shiftstack_keystone_credentials() -> keystone.KeystoneCredentialsFixture:
    return tobiko.get_fixture(ShiftstackKeystoneCredentialsFixture)
