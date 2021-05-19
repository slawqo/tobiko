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
import inspect
import typing  # noqa

import fixtures
import testtools


SkipException = testtools.TestCase.skipException  # type: typing.Type

SkipTarget = typing.Union[typing.Callable,
                          typing.Type[testtools.TestCase],
                          typing.Type[fixtures.Fixture]]
SkipDecorator = typing.Callable[[SkipTarget], SkipTarget]


def skip_test(reason: str):
    """Interrupt test case execution marking it as skipped for given reason"""
    raise SkipException(reason)


def skip(reason: str) -> SkipDecorator:
    """Mark test case for being skipped for a given reason"""
    return _skip_unless(reason, None, True)


def skip_if(reason: str, function: typing.Callable, *args, **kwargs) -> \
        SkipDecorator:
    """Mark test case for being skipped for a given reason if it matches"""
    return _skip_unless(reason, function, False, *args, **kwargs)


def skip_unless(reason: str, function: typing.Callable, *args, **kwargs) -> \
        SkipDecorator:
    """Mark test case for being skipped for a given reason unless it matches"""
    return _skip_unless(reason, function, True, *args, **kwargs)


def _skip_unless(reason: str, function: typing.Optional[typing.Callable],
                 unless: bool, *args, **kwargs) -> SkipDecorator:
    """Mark test case for being skipped for a given reason unless it matches"""

    def decorator(obj: SkipTarget) -> SkipTarget:
        method = _get_decorated_method(obj)

        @functools.wraps(method)
        def skipping_unless(*_args, **_kwargs):
            if function is not None:
                return_value = function(*args, **kwargs)
                if unless is bool(return_value):
                    return method(*_args, **_kwargs)
                if '{return_value' in reason:
                    skip_test(reason.format(return_value=return_value))
            skip_test(reason)

        if obj is method:
            return skipping_unless
        else:
            setattr(obj, method.__name__, skipping_unless)
            return obj

    return decorator


def _get_decorated_method(obj: typing.Any) -> typing.Callable:
    if inspect.isclass(obj):
        setup_method = getattr(obj, 'setUp', None)
        if callable(setup_method):
            return setup_method
        else:
            raise TypeError(f"Class {obj} does not implement setUp method")
    elif callable(obj):
        return obj
    else:
        raise TypeError(f"Object {obj} is not a class or a function")
