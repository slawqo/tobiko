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
import time

from oslo_log import log
import yaml

import tobiko
from tobiko.shell import sh

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


class WaitForCloudInitTimeoutError(tobiko.TobikoException):
    message = ("after {enlapsed_time} seconds cloud-init status of host "
               "{hostname!r} is still {actual!r} while it is expecting to "
               "be in {expected!r}")


def get_cloud_init_status(ssh_client=None, timeout=None):
    output = sh.execute('cloud-init status',
                        ssh_client=ssh_client,
                        timeout=timeout,
                        sudo=True).stdout
    return yaml.load(output)['status']


def wait_for_cloud_init_done(ssh_client=None, timeout=None,
                             sleep_interval=None):
    return wait_for_cloud_init_status(expected={'done'},
                                      ssh_client=ssh_client,
                                      timeout=timeout,
                                      sleep_interval=sleep_interval)


def wait_for_cloud_init_status(expected, ssh_client=None, timeout=None,
                               sleep_interval=None):
    expected = set(expected)
    timeout = timeout and float(timeout) or 1200.
    sleep_interval = sleep_interval and float(sleep_interval) or 5.
    start_time = time.time()
    actual = get_cloud_init_status(ssh_client=ssh_client, timeout=timeout)
    while actual not in expected:
        enlapsed_time = time.time() - start_time
        if enlapsed_time >= timeout:
            raise WaitForCloudInitTimeoutError(hostname=ssh_client.hostname,
                                               actual=actual,
                                               expected=expected,
                                               enlapsed_time=enlapsed_time)

        LOG.debug("Waiting cloud-init status on host %r to switch from %r to "
                  "%r...",
                  ssh_client.hostname, actual, expected)
        time.sleep(sleep_interval)
        actual = get_cloud_init_status(ssh_client=ssh_client,
                                       timeout=timeout-enlapsed_time)
    return actual
