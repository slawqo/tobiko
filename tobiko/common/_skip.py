# Copyright 2018 Red Hat
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

import testtools


SkipException = testtools.TestCase.skipException


def skip(reason):
    raise SkipException(reason)


def skip_if(reason, condition, *condition_args, **condition_kwargs):

    def decorator(method):

        @functools.wraps(method)
        def wrapped_method(*args, **kwargs):
            if condition(*condition_args, **condition_kwargs):
                skip(reason)
            return method(*args, **kwargs)

        return wrapped_method

    return decorator


def skip_until(reason, condition, *condition_args, **condition_kwargs):

    def decorator(method):

        @functools.wraps(method)
        def wrapped_method(*args, **kwargs):
            if not condition(*condition_args, **condition_kwargs):
                skip(reason)
            return method(*args, **kwargs)

        return wrapped_method

    return decorator
