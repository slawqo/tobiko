# Copyright (c) 2022 Red Hat, Inc.
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

import itertools
import os
import socket

import testtools

import tobiko
from tobiko import BackgroundProcessFixture


def get_sock_file() -> str:
    return tobiko.tobiko_config_path(f'~/.tobiko/tests/{__name__}/sock')


class MyBackgroundProcessFixture(BackgroundProcessFixture):

    def run(self, *args, **kwargs):
        self.serve_numbers()

    def serve_numbers(self):
        sock_file = get_sock_file()
        os.makedirs(os.path.dirname(sock_file), exist_ok=True)
        try:
            os.unlink(sock_file)
        except OSError:
            if os.path.exists(sock_file):
                raise
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.bind(sock_file)
            sock.listen(1)
            for i in itertools.count():
                connection, _client_address = sock.accept()
                try:
                    message = bytes(f'{i}', encoding='utf-8')
                    connection.send(message)
                except Exception as ex:
                    print(ex)
                finally:
                    connection.close()
        finally:
            sock.close()

    def request_number(self, timeout=30.) -> int:
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        with connection:
            for attempt in tobiko.retry(timeout=timeout):
                try:
                    connection.connect(get_sock_file())
                    break
                except (ConnectionRefusedError, FileNotFoundError) as ex:
                    if attempt.is_last:
                        raise RuntimeError('Server not running') from ex
            message = connection.recv(4096)
            return int(message)


class BackgroundProcessTest(testtools.TestCase):

    process = tobiko.required_fixture(MyBackgroundProcessFixture,
                                      setup=False)

    def test_start(self):
        self.stop_process()
        number0 = self.start_process()
        self.assertLess(number0, self.start_process(),
                        "process has been restarted")

    def test_stop(self):
        number0 = self.start_process()
        self.stop_process()
        self.assertGreaterEqual(number0, self.start_process(),
                                "process not stopped")

    def start_process(self) -> int:
        # pylint: disable=protected-access
        self.process.start()
        self.assertTrue(self.process.is_alive)
        self.assertTrue(os.path.isfile(self.process._pid_file))
        return self.process.request_number()

    def stop_process(self):
        # pylint: disable=protected-access
        self.process.stop()
        self.assertFalse(self.process.is_alive)
        self.assertFalse(os.path.isfile(self.process._pid_file))
        self.assertRaises(RuntimeError, self.process.request_number,
                          timeout=5.)
