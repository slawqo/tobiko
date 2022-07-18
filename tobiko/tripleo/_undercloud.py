# Copyright 2019 Red Hat
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

import functools
import json
import os
import typing

from oslo_log import log

import tobiko
from tobiko import config
from tobiko.openstack import keystone
from tobiko.shell import ssh
from tobiko.shell import sh
from tobiko.tripleo import _rhosp


CONF = config.CONF

LOG = log.getLogger(__name__)


def undercloud_ssh_client() -> ssh.SSHClientFixture:
    host_config = undercloud_host_config()
    if not host_config.hostname:
        raise NoSuchUndercloudHostname('No such undercloud hostname')
    return ssh.ssh_client(host=host_config.hostname,
                          **host_config.connect_parameters)


class NoSuchUndercloudHostname(tobiko.TobikoException):
    message = "Undercloud hostname not specified"


class InvalidRCFile(tobiko.TobikoException):
    message = "Invalid RC file: {rcfile}"


def fetch_os_env(rcfile, *rcfiles) -> typing.Dict[str, str]:
    rcfiles = (rcfile,) + rcfiles
    LOG.debug('Fetching OS environment variables from TripleO undercloud '
              f'host files: {",".join(rcfiles)}')
    errors = []
    for rcfile in rcfiles:
        LOG.debug(f'Reading rcfile: {rcfile}...')
        try:
            result = sh.execute(f". {rcfile}; env | grep '^OS_'",
                                ssh_client=undercloud_ssh_client())
        except sh.ShellCommandFailed as ex:
            LOG.debug(f"Unable to get overcloud RC file '{rcfile}' content "
                      f"({ex})")
            errors.append(tobiko.exc_info)
        else:
            LOG.debug(f'Parsing environment variables from: {rcfile}...')
            env = {}
            for line in result.stdout.splitlines():
                name, value = line.split('=')
                env[name] = value
            if env:
                env_dump = json.dumps(env, sort_keys=True, indent=4)
                LOG.debug(f'Environment variables read from: {rcfile}:\n'
                          f'{env_dump}')
                return env
    for error in errors:
        LOG.exception(f"Unable to get overcloud RC file '{rcfile}' "
                      "content", exc_info=error)
    raise InvalidRCFile(rcfile=", ".join(rcfiles))


def load_undercloud_rcfile() -> typing.Dict[str, str]:
    return fetch_os_env(*CONF.tobiko.tripleo.undercloud_rcfile)


class EnvironUndercloudKeystoneCredentialsFixture(
        keystone.EnvironKeystoneCredentialsFixture):
    def get_environ(self) -> typing.Dict[str, str]:
        return load_undercloud_rcfile()


class CloudsFileUndercloudKeystoneCredentialsFixture(
        keystone.CloudsFileKeystoneCredentialsFixture):

    def __init__(self, credentials=None, cloud_name=None,
                 clouds_content=None, clouds_file=None, clouds_files=None):
        cloud_name = cloud_name or load_undercloud_rcfile()['OS_CLOUD']

        super(CloudsFileUndercloudKeystoneCredentialsFixture, self).__init__(
            credentials=credentials, cloud_name=cloud_name,
            clouds_content=clouds_content, clouds_file=clouds_file,
            clouds_files=clouds_files)


class HasUndercloudFixture(tobiko.SharedFixture):

    has_undercloud: typing.Optional[bool] = None

    def setup_fixture(self):
        self.has_undercloud = check_undercloud()


def check_undercloud() -> bool:
    try:
        ssh_client = undercloud_ssh_client()
    except NoSuchUndercloudHostname:
        LOG.debug('TripleO undercloud hostname not found')
        return False
    try:
        ssh_client.connect(retry_count=1,
                           connection_attempts=1,
                           timeout=15.)
    except Exception as ex:
        LOG.debug(f'Unable to connect to TripleO undercloud host: {ex}',
                  exc_info=1)
        return False

    LOG.debug('TripleO undercloud host found')
    return True


def has_undercloud() -> bool:
    return tobiko.setup_fixture(HasUndercloudFixture).has_undercloud


skip_if_missing_undercloud = tobiko.skip_unless(
    'TripleO undercloud hostname not configured', has_undercloud)


class UndecloudHostConfig(tobiko.SharedFixture):

    hostname: typing.Optional[str] = None
    port: typing.Optional[int] = None
    username: typing.Optional[str] = None

    def __init__(self, **kwargs):
        super(UndecloudHostConfig, self).__init__()
        self._connect_parameters = ssh.gather_ssh_connect_parameters(**kwargs)
        self.key_filename: typing.List[str] = []

    def setup_fixture(self):
        self.hostname = CONF.tobiko.tripleo.undercloud_ssh_hostname.strip()
        self.port = CONF.tobiko.tripleo.undercloud_ssh_port
        self.username = CONF.tobiko.tripleo.undercloud_ssh_username
        self.key_filename = self.get_key_filenames()

    @staticmethod
    def get_key_filenames() -> typing.List[str]:
        key_filenames: typing.List[str] = []
        conf = tobiko.tobiko_config()
        key_filename = conf.tripleo.undercloud_ssh_key_filename
        if key_filename:
            key_filename = tobiko.tobiko_config_path(key_filename)
            if os.path.isfile(key_filename):
                key_filenames.append(key_filename)
        key_filenames.extend(ssh.list_proxy_jump_key_filenames())
        key_filenames.extend(ssh.list_key_filenames())
        return tobiko.select_uniques(key_filenames)

    @property
    def connect_parameters(self):
        parameters = ssh.gather_ssh_connect_parameters(self)
        parameters.update(self._connect_parameters)
        return parameters


def undercloud_host_config() -> UndecloudHostConfig:
    return tobiko.setup_fixture(UndecloudHostConfig)


def undercloud_keystone_client():
    session = undercloud_keystone_session()
    return keystone.get_keystone_client(session=session)


def _get_keystone_credentials():
    environ = load_undercloud_rcfile()
    if 'OS_CLOUD' in environ:
        credentials = CloudsFileUndercloudKeystoneCredentialsFixture
    else:
        credentials = EnvironUndercloudKeystoneCredentialsFixture
    return credentials


def undercloud_keystone_session():
    return keystone.get_keystone_session(
        credentials=_get_keystone_credentials())


def undercloud_keystone_credentials():
    return tobiko.setup_fixture(_get_keystone_credentials()).credentials


@functools.lru_cache()
def undercloud_version() -> tobiko.Version:
    ssh_client = undercloud_ssh_client()
    return _rhosp.get_rhosp_version(connection=ssh_client)
