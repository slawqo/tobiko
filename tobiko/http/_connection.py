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

from urllib3 import connection
from urllib3 import connectionpool

from tobiko.shell import ssh


class HTTPConnection(connection.HTTPConnection):

    def __init__(self, *args, **kwargs):
        #: Port forwarding address to redirect connection too if given
        self.forward_address = kwargs.pop("forward_address", None)
        super(HTTPConnection, self).__init__(*args, **kwargs)

    def _new_conn(self):
        """ Establish a socket connection and set nodelay settings on it.

        :return: New socket connection.
        """
        extra_kw = {}
        if self.source_address:
            extra_kw["source_address"] = self.source_address

        if self.socket_options:
            extra_kw["socket_options"] = self.socket_options

        address = self.forward_address or (self._dns_host, self.port)
        try:
            conn = connection.connection.create_connection(
                address, self.timeout, **extra_kw)

        except connection.SocketTimeout as ex:
            raise connection.ConnectTimeoutError(
                self, (f"Connection to {self.host} timed out. "
                       f"(connect timeout={self.timeout})")) from ex

        except connection.SocketError as ex:
            raise connection.NewConnectionError(
                self, f"Failed to establish a new connection: {ex}") from ex

        return conn


class HTTPSConnection(HTTPConnection, connection.HTTPSConnection):
    pass


class HTTPConnectionPool(connectionpool.HTTPConnectionPool):

    ConnectionCls = HTTPConnection

    def __init__(self, host, port, ssh_client=None, **kwargs):
        forward_address = ssh.get_forward_port_address(address=(host, port),
                                                       ssh_client=ssh_client)
        super(HTTPConnectionPool, self).__init__(
            host=host, port=port, forward_address=forward_address, **kwargs)


class HTTPSConnectionPool(HTTPConnectionPool,
                          connectionpool.HTTPSConnectionPool):

    ConnectionCls = HTTPSConnection
