# Copyright (c) 2019 Red Hat, Inc.
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
from urllib import parse
import typing

from oslo_log import log

from tobiko.docker import _exception
from tobiko.shell import sh
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


def discover_docker_urls(
        ssh_client: ssh.SSHClientType = None,
        default_url='unix:/var/run/docker.sock',
        check_urls=True,
        sudo=False):
    urls = []
    processes = sh.list_processes(command='^dockerd',
                                  ssh_client=ssh_client,
                                  sudo=sudo)

    for process in processes:
        if process.command_line:
            urls += urls_from_command_line(process.command_line)

    urls.append(default_url)
    urls = list(collections.OrderedDict.fromkeys(urls))

    error: typing.Optional[Exception] = None
    if check_urls:
        valid_urls = []
        for url in urls:
            parsed_url = parse.urlparse(url)
            if (parsed_url.scheme == 'unix' and
                    parsed_url.path.startswith('/')):
                try:
                    sh.execute(f"test -r '{parsed_url.path}'",
                               ssh_client=ssh_client,
                               sudo=sudo)
                except sh.ShellCommandFailed as ex:
                    LOG.exception(
                        f"Can't read from socket: {parsed_url.path}")
                    ex.__cause__ = error
                    error = ex
                else:
                    valid_urls.append(url)

        if not valid_urls:
            raise _exception.DockerUrlNotFoundError(
                "Docker is not running") from error
        urls = valid_urls
    return urls


def urls_from_command_line(command_line: sh.ShellCommand,
                           default_url='unix:/var/run/docker.sock') \
        -> typing.List[str]:
    urls = []
    arg_is_url = False
    for arg in command_line[1:]:
        if arg == '-H':
            arg_is_url = True
            continue
        if arg_is_url:
            arg_is_url = False
            try:
                url = parse.urlparse(arg)
            except Exception:
                LOG.debug(f'Invalid URL: {arg}', exc_info=1)
                continue
            if url.scheme == 'fd':
                urls.append(default_url)
                continue
            if url.scheme != 'unix':
                LOG.debug(f'Unsupported URL scheme: {arg}')
                continue
            if not url.path.startswith('/'):
                LOG.debug(f'Unsupported URL path: {arg}')
                continue
            urls.append(arg)
    return urls


def is_docker_running(ssh_client=None, sudo=False, **execute_params):
    try:
        discover_docker_urls(ssh_client=ssh_client,
                             sudo=sudo,
                             **execute_params)
    except _exception.DockerUrlNotFoundError:
        return False
    else:
        return True
