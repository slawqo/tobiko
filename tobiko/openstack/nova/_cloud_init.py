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

import collections
import contextlib
import typing

from oslo_log import log
import yaml

import tobiko
from tobiko.shell import sh
from tobiko.shell import ssh

LOG = log.getLogger(__name__)


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
            if not isinstance(obj, collections.abc.Mapping):
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
        return '#cloud-config\n' + yaml.dump(dict(self))

    def __add__(self, other):
        return combine_cloud_configs([self, other])


class InvalidCloudInitStatusError(tobiko.TobikoException):
    message = ("cloud-init status of host '{hostname}' is "
               "'{actual_status}' while it is expecting to "
               "be in {expected_states!r}:\n"
               "{details}")


class WaitForCloudInitTimeoutError(InvalidCloudInitStatusError):
    message = ("after {timeout} seconds cloud-init status of host "
               "'{hostname}' is still '{actual_status}' while it is "
               "expecting to be in {expected_states!r}:\n"
               "{details}")


COUD_INIT_TRANSIENT_STATES = {
    'done': tuple(['running'])
}


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

    status = yaml.load(output)
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
    hostname = getattr(ssh_client, 'hostname', None)
    if transient_states is None:
        transient_states = list()
        for status in expected_states:
            transient_states += COUD_INIT_TRANSIENT_STATES.get(status, [])

    with open_cloud_init_ouput(timeout=timeout,
                               ssh_client=ssh_client) as output:
        for attempt in tobiko.retry(timeout=timeout,
                                    interval=sleep_interval,
                                    default_timeout=600.,
                                    default_interval=5.):
            actual_status = get_cloud_init_status(ssh_client=ssh_client,
                                                  timeout=attempt.time_left)
            if actual_status in expected_states:
                return actual_status

            output.readall()
            if actual_status not in transient_states:
                raise InvalidCloudInitStatusError(
                    hostname=hostname,
                    actual_status=actual_status,
                    expected_states=expected_states,
                    details=str(output))

            try:
                attempt.check_limits()
            except tobiko.RetryTimeLimitError as ex:
                raise WaitForCloudInitTimeoutError(
                    timeout=attempt.timeout,
                    hostname=hostname,
                    actual_status=actual_status,
                    expected_states=expected_states,
                    details=str(output)) from ex

            # show only the last 10 lines
            details = '\n'.join(str(output).splitlines()[-10:])
            LOG.debug(f"Waiting cloud-init status on host '{hostname}' to "
                      f"switch from '{actual_status}' to any of expected "
                      f"states ({', '.join(expected_states)})\n\n"
                      f"{details}\n")

    raise RuntimeError("Retry loop ended himself")


CLOUD_INIT_OUTPUT_FILE = '/var/log/cloud-init-output.log'


@contextlib.contextmanager
def open_cloud_init_ouput(
        cloud_init_output_file: str = CLOUD_INIT_OUTPUT_FILE,
        tail=False,
        follow=False,
        **params) \
        -> typing.Generator[sh.ShellStdout, None, None]:
    command = ['tail']
    if not tail:
        # Start from the begin of the file
        command += ['-c', '+0']
    if follow:
        command += ['-F']

    command += [cloud_init_output_file]
    process = sh.process(command, **params)
    with process:
        yield process.stdout
