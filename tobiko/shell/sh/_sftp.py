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

import shutil
import typing

from oslo_log import log
import paramiko

from tobiko.shell import ssh


LOG = log.getLogger(__name__)

SSHClientType = typing.Union[None, ssh.SSHClientFixture, bool]


def sftp_client(ssh_client: SSHClientType) \
        -> typing.Optional[paramiko.SFTPClient]:
    if ssh_client is None:
        ssh_client = ssh.ssh_proxy_client()
    if isinstance(ssh_client, ssh.SSHClientFixture):
        return ssh_client.connect().open_sftp()
    assert ssh_client is None
    return None


def put_file(local_file: str,
             remote_file: str,
             ssh_client: SSHClientType = None):
    sftp = sftp_client(ssh_client)
    if sftp is None:
        LOG.debug(f"Copy local file: '{local_file}' -> '{remote_file}' ...")
        shutil.copyfile(local_file, remote_file)
    else:
        LOG.debug(f"Put remote file: '{local_file}' -> '{remote_file}' ...")
        with sftp:
            sftp.put(local_file, remote_file)


def get_file(remote_file: str,
             local_file: str,
             ssh_client: SSHClientType = None):
    sftp = sftp_client(ssh_client)
    if sftp is None:
        LOG.debug(f"Copy local file: '{remote_file}' -> '{local_file}' ...")
        shutil.copyfile(remote_file, local_file)
    else:
        LOG.debug(f"Get remote file: '{remote_file}' -> '{local_file}' ...")
        with sftp:
            sftp.get(remote_file, local_file)
