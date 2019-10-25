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
import contextlib
import socket

import netaddr
from oslo_log import log
import six
from six.moves import urllib
import sshtunnel

import tobiko

LOG = log.getLogger(__name__)


class SSHTunnelForwarderFixture(tobiko.SharedFixture):

    forwarder = None

    def __init__(self, ssh_client):
        super(SSHTunnelForwarderFixture, self).__init__()
        self.ssh_client = ssh_client
        self._forwarding = collections.OrderedDict()

    def put_forwarding(self, remote_address, remote_port=None,
                       local_address=None, local_port=None):
        remote = AddressPair.create(remote_address, remote_port)
        local = AddressPair.create(local_address, local_port)
        return self._forwarding.setdefault(remote, local)

    def get_forwarding(self, remote_address, remote_port=None):
        remote = AddressPair.create(remote_address, remote_port)
        return self._forwarding.get(remote)

    def setup_fixture(self):
        self.setup_forwarder()

    def setup_forwarder(self):
        forwarder = self.forwarder
        if not forwarder:
            remote_bind_addresses = list(self._forwarding.keys())
            local_bind_addresses = list(self._forwarding.values())
            self.forwarder = forwarder = SSHTunnelForwarder(
                ssh_client=self.ssh_client,
                local_bind_addresses=local_bind_addresses,
                remote_bind_addresses=remote_bind_addresses)
            self.addCleanup(self.cleanup_forwarder)
            forwarder.start()
            self.ssh_client.addCleanup(self)

        return forwarder

    def cleanup_forwarder(self):
        forwarder = self.forwarder
        if forwarder:
            del self.forwarder
            forwarder.stop()


class SSHTunnelForwarder(sshtunnel.SSHTunnelForwarder):

    daemon_forward_servers = True  #: flag tunnel threads in daemon mode
    daemon_transport = True  #: flag SSH transport thread in daemon mode

    def __init__(self, ssh_client, **kwargs):
        self.ssh_client = ssh_client
        params = self._merge_parameters(self._get_connect_parameters(),
                                        **kwargs)
        super(SSHTunnelForwarder, self).__init__(**params)

    def _merge_parameters(self, *dicts, **kwargs):
        result = {}
        for d in dicts + (kwargs,):
            if d:
                result.update((k, v) for k, v in d.items() if v is not None)
        return result

    @staticmethod
    def _consolidate_auth(ssh_password=None,
                          ssh_pkey=None,
                          ssh_pkey_password=None,
                          allow_agent=True,
                          host_pkey_directories=None,
                          logger=None):
        return None, None

    def _get_connect_parameters(self):
        parameters = self.ssh_client.setup_connect_parameters()
        return dict(ssh_address_or_host=parameters['hostname'],
                    ssh_username=parameters.get('username'),
                    ssh_password=parameters.get('password'),
                    ssh_pkey=parameters.get('pkey'),
                    ssh_port=parameters.get('port'),
                    ssh_private_key_password=parameters.get('passphrase'),
                    compression=parameters.get('compress'),
                    allow_agent=parameters.get('allow_agent'))

    def _connect_to_gateway(self):
        # pylint: disable=attribute-defined-outside-init
        self._transport = self._get_transport()

    def _get_transport(self):
        return self.ssh_client.connect().get_transport()

    def _stop_transport(self):
        if self.is_active:
            del self._transport
            assert not self.is_active
        super(SSHTunnelForwarder, self)._stop_transport()


class AddressPair(collections.namedtuple('AddressPair', ['host', 'port'])):

    @classmethod
    def create(cls, address=None, port=None):
        port = port and int(port) or None
        address = address or '127.0.0.1'
        if isinstance(address, netaddr.IPAddress):
            if port is None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                with contextlib.closing(sock):
                    sock.bind((str(address), 0))
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    return cls(*sock.getsockname())
            else:
                return cls(str(address), port)
        elif isinstance(address, urllib.parse.ParseResult):
            return cls(address.hostname or address.path, address.port or None)
        elif isinstance(address, six.string_types):
            try:
                return cls.create(netaddr.IPAddress(address), port)
            except ValueError:
                pass
            if port is None:
                return cls.create(urllib.parse.urlparse(address))
            else:
                return cls(address.lower(), port)
        elif isinstance(address, collections.Sequence):
            return cls.create(*address)

        message = ("Invalid address pair parameters: "
                   "address={!r}, port={!r}").format(address, port)
        raise TypeError(message)
