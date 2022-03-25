# Copyright (c) 2021 Red Hat, Inc.
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

import multiprocessing
from multiprocessing import pool
import typing

import tobiko
from tobiko.run import _config


class WorkersPoolFixture(tobiko.SharedFixture):

    config = tobiko.required_fixture(_config.RunConfigFixture)

    pool: pool.Pool
    workers_count: int = 0

    def __init__(self, workers_count: int = None):
        super().__init__()
        if workers_count is not None:
            self.workers_count = workers_count

    def setup_fixture(self):
        workers_count = self.workers_count
        if not workers_count:
            workers_count = self.config.workers_count
        self.workers_count = workers_count or 0
        context = multiprocessing.get_context('spawn')
        self.pool = context.Pool(processes=workers_count or None)


def workers_pool() -> pool.Pool:
    return tobiko.setup_fixture(WorkersPoolFixture).pool


def call_async(func: typing.Callable,
               *args,
               **kwargs):
    return workers_pool().apply_async(func, args=args, kwds=kwargs)
