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

from collections import abc
import typing

from oslo_log import log

import tobiko
from tobiko.shell import sh
from tobiko.shell import ssh

LOG = log.getLogger(__name__)


CLOUD_INIT_TRANSIENT_STATES = {
    'done': ('running',)
}

CLOUD_INIT_OUTPUT_FILE = '/var/log/cloud-init-output.log'
CLOUD_INIT_LOG_FILE = '/var/log/cloud-init.log'


def user_data(*args, **kwargs):
    config = cloud_config(*args, **kwargs)
    if config:
        return config.user_data
    else:
        return ''


def cloud_config(*args, **kwargs):
    return combine_cloud_configs(args + (kwargs,))


def combine_cloud_configs(objs):
    packages = []
    runcmd = []
    extra_params = {}
    for obj in objs:
        if obj:
            if not isinstance(obj, abc.Mapping):
                obj = dict(obj)
            for package in obj.pop('packages', []):
                if package and package not in packages:
                    packages.append(package)
            for cmdline in obj.pop('runcmd', []):
                if cmdline:
                    cmdline = list(sh.shell_command(cmdline))
                    if cmdline:
                        runcmd.append(cmdline)
            if obj:
                extra_params.update(obj)

    return CloudConfig.create(packages=packages or None,
                              runcmd=runcmd or None,
                              **extra_params)


class CloudConfig(dict):

    @classmethod
    def create(cls, **kwargs):
        return cls((k, v)
                   for k, v in kwargs.items()
                   if v is not None)

    @property
    def user_data(self):
        return '#cloud-config\n' + tobiko.dump_yaml(dict(self))

    def __add__(self, other):
        return combine_cloud_configs([self, other])

    @property
    def packages(self) -> typing.List[str]:
        return self.setdefault('packages', [])

    def add_package(self, *packages: str):
        _packages = self.packages
        for package in packages:
            tobiko.check_valid_type(package, str)
            if package not in _packages:
                _packages.append(package)

    @property
    def runcmd(self) -> typing.List[typing.List[str]]:
        return self.setdefault('runcmd', [])

    def add_runcmd(self, *command_lines: sh.ShellCommandType):
        runcmd = self.runcmd
        for command_line in command_lines:
            command_line = sh.shell_command(command_line)
            runcmd.append(list(command_line))

    @property
    def write_files(self) -> typing.List[typing.Dict[str, typing.Any]]:
        return self.setdefault('write_files', [])

    def add_write_file(self,
                       path: str,
                       content: str,
                       owner: str = None,
                       permissions: str = None):
        tobiko.check_valid_type(path, str)
        tobiko.check_valid_type(content, str)
        entry = dict(path=path, content=content)
        if owner is not None:
            tobiko.check_valid_type(owner, str)
            entry['owner'] = owner
        if permissions is not None:
            tobiko.check_valid_type(owner, str)
            entry['permission'] = permissions
        self.write_files.append(entry)


class InvalidCloudInitStatusError(tobiko.TobikoException):
    message = ("cloud-init status of host '{hostname}' is "
               "'{actual_status}' while it is expecting to "
               "be in {expected_states!r}:\n\n"
               f"--- {CLOUD_INIT_LOG_FILE} ---\n"
               "{log_file}\n\n"
               f"--- {CLOUD_INIT_OUTPUT_FILE} ---\n"
               "{output_file}\n\n")


class WaitForCloudInitTimeoutError(InvalidCloudInitStatusError):
    message = ("after {timeout} seconds cloud-init status of host "
               "'{hostname}' is still '{actual_status}' while it is "
               "expecting to be in {expected_states!r}:\n\n"
               f"--- {CLOUD_INIT_LOG_FILE} ---\n"
               "{log_file}\n\n"
               f"--- {CLOUD_INIT_OUTPUT_FILE} ---\n"
               "{output_file}\n\n")


def get_cloud_init_status(
        ssh_client: typing.Optional[ssh.SSHClientFixture] = None,
        timeout: tobiko.Seconds = None) \
        -> str:
    try:
        output = sh.execute('cloud-init status',
                            ssh_client=ssh_client,
                            timeout=timeout,
                            sudo=True).stdout
    except sh.ShellCommandFailed as ex:
        output = ex.stdout
        if output:
            LOG.debug(f"Cloud init status error reported:\n{ex}")
        else:
            raise

    status = tobiko.load_yaml(output)
    tobiko.check_valid_type(status, dict)
    tobiko.check_valid_type(status['status'], str)
    return status['status']


def wait_for_cloud_init_done(
        ssh_client: typing.Optional[ssh.SSHClientFixture] = None,
        timeout: tobiko.Seconds = None,
        sleep_interval: tobiko.Seconds = None) \
        -> str:
    return wait_for_cloud_init_status('done',
                                      ssh_client=ssh_client,
                                      timeout=timeout,
                                      sleep_interval=sleep_interval)


def wait_for_cloud_init_status(
        *expected_states: str,
        transient_states: typing.Optional[typing.Container[str]] = None,
        ssh_client: typing.Optional[ssh.SSHClientFixture] = None,
        timeout: tobiko.Seconds = None,
        sleep_interval: tobiko.Seconds = None) \
        -> str:
    hostname = sh.get_hostname(ssh_client=ssh_client,
                               timeout=timeout)
    if transient_states is None:
        transient_states = list()
        for status in expected_states:
            transient_states += CLOUD_INIT_TRANSIENT_STATES.get(status, [])

    def _read_file(filename: str, tail=False) -> str:
        return read_file(filename=filename,
                         ssh_client=ssh_client,
                         timeout=timeout,
                         tail=tail)

    actual_status: typing.Optional[str]

    for attempt in tobiko.retry(timeout=timeout,
                                interval=sleep_interval,
                                default_timeout=1200.,
                                default_interval=5.):
        try:
            actual_status = get_cloud_init_status(ssh_client=ssh_client,
                                                  timeout=attempt.time_left)
        except sh.ShellCommandFailed:
            LOG.exception('Unable to get cloud-init status')
            actual_status = None
        else:
            if actual_status in expected_states:
                break

        if attempt.is_last:
            raise WaitForCloudInitTimeoutError(
                timeout=attempt.timeout,
                hostname=hostname,
                actual_status=actual_status,
                expected_states=expected_states,
                log_file=_read_file(CLOUD_INIT_LOG_FILE),
                output_file=_read_file(CLOUD_INIT_OUTPUT_FILE))

        elif actual_status in transient_states:
            last_log_lines = _read_file(CLOUD_INIT_LOG_FILE, tail=True)
            LOG.debug(f"Waiting cloud-init status on host '{hostname}' to "
                      f"switch from '{actual_status}' to any of expected "
                      f"states ({', '.join(expected_states)}):\n\n"
                      f"--- {CLOUD_INIT_LOG_FILE} ---\n"
                      f"{last_log_lines}\n\n")
        else:
            raise InvalidCloudInitStatusError(
                hostname=hostname,
                actual_status=actual_status,
                expected_states=expected_states,
                log_file=_read_file(CLOUD_INIT_LOG_FILE),
                output_file=_read_file(CLOUD_INIT_OUTPUT_FILE))

    else:
        raise RuntimeError('Broken retry loop')
    return actual_status


def read_file(filename: str,
              tail=False,
              ssh_client: ssh.SSHClientType = None,
              timeout: tobiko.Seconds = None):
    if tail:
        command = 'tail'
    else:
        command = 'cat'
    try:
        return sh.execute(f'{command} "{filename}"',
                          timeout=timeout,
                          ssh_client=ssh_client).stdout
    except sh.ShellCommandFailed:
        LOG.exception(f"Error reading file '{filename}'")
        return ""
