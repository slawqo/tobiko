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

import json
import os
import inspect
import sys

import fixtures
from oslo_log import log
import six
import testtools

import tobiko
from tobiko.common import _detail
from tobiko.common import _exception


LOG = log.getLogger(__name__)


def is_fixture(obj):
    '''Returns whenever obj is a fixture or not'''
    return (getattr(obj, '__tobiko_fixture__', False) or
            isinstance(obj, fixtures.Fixture) or
            (inspect.isclass(obj) and issubclass(obj, fixtures.Fixture)))


def get_fixture(obj, fixture_id=None, manager=None):
    '''Returns a fixture identified by given :param obj:

    It returns registered fixture for given :param obj:. If none has been
    registered it creates a new one.

    :param obj: can be:
      - an instance of fixtures.Fixture class: on such case it would return
        obj itself
      - the unique fully qualified name or an object that refers to a fixture
        class or an instance to a fixture.
      - the class of the fixture. It must be a subclass of fixtures.Fixture
        sub-class.

    :returns: an instance of fixture class identified by obj, or obj itself
    if it is instance of fixtures.Fixture class.

    '''
    if isinstance(obj, fixtures.Fixture):
        return obj
    else:
        manager = manager or FIXTURES
        return manager.get_fixture(obj, fixture_id=fixture_id)


def get_fixture_name(obj):
    '''Get unique fixture name'''
    name = getattr(obj, '__tobiko_fixture_name__', None)
    if name is None:
        if not is_fixture(obj):
            raise TypeError('Object {obj!r} is not a fixture.'.format(obj=obj))
        name = get_object_name(obj)
        obj.__tobiko_fixture__ = True
        obj.__tobiko_fixture_name__ = name
    return name


def get_fixture_class(obj):
    '''Get fixture class'''
    if isinstance(obj, six.string_types):
        obj = tobiko.load_object(obj)

    if not inspect.isclass(obj):
        obj = type(obj)

    assert issubclass(obj, fixtures.Fixture)
    return obj


def get_fixture_dir(obj):
    '''Get directory of fixture class source code file'''
    return os.path.dirname(inspect.getfile(get_fixture_class(obj)))


def remove_fixture(obj, fixture_id=None, manager=None):
    '''Unregister fixture identified by given :param obj: if any'''
    manager = manager or FIXTURES
    return manager.remove_fixture(obj, fixture_id=fixture_id)


def setup_fixture(obj, fixture_id=None, manager=None, alternative=None):
    '''Get registered fixture and setup it up'''
    if alternative is None:
        objs = [obj]
    else:
        objs = [obj, alternative]
    with _exception.handle_multiple_exceptions(
            handle_exception=handle_setup_error):
        errors = []
        for _obj in objs:
            fixture = get_fixture(_obj, fixture_id=fixture_id, manager=manager)
            try:
                fixture.setUp()
                break
            except testtools.MultipleExceptions:
                errors.append(sys.exc_info())
        else:
            raise testtools.MultipleExceptions(*errors)

    return fixture


def handle_setup_error(ex_type, ex_value, ex_tb):
    if issubclass(ex_type, fixtures.SetupError):
        details = ex_value.args[0]
        if details:
            details = {k: v.as_text() for k, v in details.items()}
            pretty_details = json.dumps(details, indent=4, sort_keys=True)
            LOG.debug(f"Fixture setup error details:\n{pretty_details}\n")
    else:
        LOG.exception("Unhandled setup exception",
                      exc_info=(ex_type, ex_value, ex_tb))


def reset_fixture(obj, fixture_id=None, manager=None):
    '''Get registered fixture and reset it'''
    fixture = get_fixture(obj, fixture_id=fixture_id, manager=manager)
    with _exception.handle_multiple_exceptions():
        fixture.reset()
    return fixture


def cleanup_fixture(obj, fixture_id=None, manager=None):
    '''Get registered fixture and clean it up'''
    fixture = get_fixture(obj, fixture_id=fixture_id, manager=manager)
    with _exception.handle_multiple_exceptions():
        fixture.cleanUp()
    return fixture


def get_name_and_object(obj):
    '''Get (name, obj) tuple identified by given :param obj:'''
    if isinstance(obj, six.string_types):
        return obj, tobiko.load_object(obj)
    else:
        return get_object_name(obj), obj


def visit_objects(objects):
    if not isinstance(objects, list):
        raise TypeError("parameter 'objects' is not a list")

    visited = set()
    while objects:
        obj = objects.pop()
        try:
            name, obj = get_name_and_object(obj)
        except Exception:
            LOG.exception('Unable to get (name, object) pair from {!r}'.format(
                obj))
        else:
            if name not in visited:
                visited.add(name)
                yield name, obj


def list_required_fixtures(objects):
    '''List fixture names required by given objects'''
    result = []
    objects = list(objects)
    for name, obj in visit_objects(objects):
        if is_fixture(obj):
            result.append(name)
            if not inspect.isclass(obj):
                obj = type(obj)

        elif is_test_method(obj):
            # Test methods also require test class fixtures
            if '.' in name:
                parent_name = name.rsplit('.', 1)[0]
                objects.append(parent_name)

        objects.extend(get_required_fixtures(obj))

    result.sort()
    return result


def is_test_method(obj):
    '''Returns whenever given object is a test method'''
    return ((inspect.isfunction(obj) or inspect.ismethod(obj)) and
            obj.__name__.startswith('test_'))


def get_required_fixtures(obj):
    '''Get fixture names required by given :param obj:'''
    required_names = getattr(obj, '__tobiko_required_fixtures__', None)
    if required_names is None:
        if is_test_method(obj):
            # Get fixtures from default values that are fixtures
            required = {default
                        for default in six.get_function_defaults(obj) or []
                        if is_fixture(default)}

        elif inspect.isclass(obj):
            # Get fixtures from members of type RequiredFixtureProperty
            required = {prop.fixture
                        for prop in get_required_fixture_properties(obj)}
        else:
            # Other types have no fixtures
            required = set()

        # Return every fixture name only once
        required_names = sorted([get_fixture_name(fixture)
                                 for fixture in required])
        try:
            # try to cache list for later use
            obj.__tobiko_required_fixtures__ = required_names
        except AttributeError:
            pass

    return required_names


def get_required_fixture_properties(cls):
    """Get list of members of type RequiredFixtureProperty of given class"""

    # inspect.getmembers() would iterate over such many testtools.TestCase
    # members too, so let exclude members from those very common base classes
    # that we know doesn't have members of type RequiredFixtureProperty
    base_classes = cls.__mro__
    for base_class in [testtools.TestCase, SharedFixture]:
        if issubclass(cls, base_class):
            base_classes = base_classes[:base_classes.index(base_class)]
            break

    # Get all members for selected class without calling properties or methods
    members = {}
    for base_class in reversed(base_classes):
        members.update(base_class.__dict__)

    # Return all members that are instances of RequiredFixtureProperty
    return [member
            for _, member in sorted(members.items())
            if isinstance(member, RequiredFixtureProperty)]


def init_fixture(obj, name):
    if inspect.isclass(obj) and issubclass(obj, fixtures.Fixture):
        try:
            obj = obj()
        except Exception as ex:
            raise TypeError(f"Error creating fixture '{name}' from class "
                            f"{obj!r}.") from ex
    if isinstance(obj, fixtures.Fixture):
        obj.__tobiko_fixture__ = True
        obj.__tobiko_fixture_name__ = name
        return obj

    raise TypeError(f"Invalid fixture object type: '{obj!r}'")


def fixture_property(*args, **kwargs):
    return FixtureProperty(*args, **kwargs)


def required_fixture(obj, **params):
    '''Creates a property that gets fixture identified by given :param obj:

    '''
    return RequiredFixtureProperty(obj, **params)


def required_setup_fixture(obj, **params):
    '''Creates a property that sets up fixture identified by given :param obj:

    '''
    return RequiredSetupFixtureProperty(obj, **params)


def get_object_name(obj):
    '''Gets a fully qualified name for given :param obj:'''
    if isinstance(obj, six.string_types):
        return obj

    name = getattr(obj, '__tobiko_fixture_name__', None)
    if name:
        return name

    if (not inspect.isfunction(obj) and
            not inspect.ismethod(obj) and
            not inspect.isclass(obj)):
        obj = type(obj)

    module = inspect.getmodule(obj).__name__

    if six.PY2:
        # Below code is only for old Python versions
        if inspect.isclass(obj):
            # This doesn't work for nested classes
            return module + '.' + obj.__name__

        method_class = getattr(obj, 'im_class', None)
        if method_class:
            # This doesn't work for nested classes
            return module + '.' + method_class.__name__ + '.' + obj.__name__

        if inspect.isfunction(obj):
            return module + '.' + obj.func_name

    else:
        # Only Python 3 defines __qualname__
        name = getattr(obj, '__qualname__', None)
        if name:
            return module + '.' + name

    msg = "Unable to get fixture name from object {!r}".format(obj)
    raise TypeError(msg)


class FixtureManager(object):

    def __init__(self):
        self.fixtures = {}

    def get_fixture(self, obj, fixture_id=None, init=None):
        name, obj = get_name_and_object(obj)
        if fixture_id:
            name += '-' + str(fixture_id)
        fixture = self.fixtures.get(name)
        if fixture is None:
            init = init or self.init_fixture
            self.fixtures[name] = fixture = init(obj=obj, name=name)
            assert isinstance(fixture, fixtures.Fixture)
        return fixture

    def init_fixture(self, obj, name):
        return init_fixture(obj=obj, name=name)

    def remove_fixture(self, obj, fixture_id=None):
        name = get_object_name(obj)
        if fixture_id:
            name += '-' + str(fixture_id)
        return self.fixtures.pop(name, None)


FIXTURES = FixtureManager()


class SharedFixture(fixtures.Fixture):
    """Base class for fixtures intended to be shared between multiple tests

    Make sure that fixture setUp method can be called more than once, but
    actually executing _setUp method only the first time. This allows the
    fixture to be passed to useFixture methods multiple times without caring
    about if has already been used before.

    Fixture set up can anyway be forced by calling 'setup_shared_fixture'
    method.

    Because cleanup policy in a shared fixture is different from a common
    fixture, cleanUp method simply doesn't nothing.

    Actual fixture cleanup is executed by calling
    cleanup_shared_fixture method.

    """

    _setup_executed = False
    _cleanup_executed = False

    __tobiko_fixture__ = True
    __tobiko_fixture_name__ = None

    def __init__(self):
        # make sure class states can be used before setUp
        self._clear_cleanups()

    @classmethod
    def get(cls, manager=None):
        return get_fixture(cls, manager=manager)

    def _remove_state(self):
        # make sure class states can be used after cleanUp
        super(SharedFixture, self)._clear_cleanups()

    def setUp(self):
        """Executes _setUp/setup_fixture method only the first time is called

        """
        if not self._setup_executed:
            LOG.debug('Set up fixture %r', self.fixture_name)
            super(SharedFixture, self).setUp()
            self._cleanup_executed = False
            self._setup_executed = True

    def cleanUp(self, raise_first=True):
        """Executes registered cleanups if any"""
        if not self._cleanup_executed:
            LOG.debug('Clean up fixture %r', self.fixture_name)
            self.addCleanup(self.cleanup_fixture)
        result = super(SharedFixture, self).cleanUp(raise_first=raise_first)
        self._setup_executed = False
        self._cleanup_executed = True
        return result

    def __enter__(self):
        return setup_fixture(self)

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa
        cleanup_fixture(self)
        return False  # propagate exceptions from the with body.

    def _setUp(self):
        self.setup_fixture()

    @property
    def fixture_name(self):
        return get_fixture_name(self)

    def setup_fixture(self):
        pass

    def cleanup_fixture(self):
        pass


class FixtureProperty(property):

    def __get__(self, instance, owner):
        instance = instance or tobiko.get_fixture(owner)
        return super(FixtureProperty, self).__get__(instance, owner)


class RequiredFixtureProperty(object):

    def __init__(self, fixture, **params):
        self.fixture = fixture
        self.fixture_params = params

    def __get__(self, instance, _):
        if instance is None:
            return self
        else:
            return self.get_fixture(instance)

    def get_fixture(self, _instance):
        return get_fixture(self.fixture, **self.fixture_params)

    @property
    def __tobiko_required_fixtures__(self):
        return [self.fixture]


class RequiredSetupFixtureProperty(RequiredFixtureProperty):

    def get_fixture(self, _instance):
        fixture = setup_fixture(self.fixture, **self.fixture_params)
        if (hasattr(_instance, 'addCleanup') and
                hasattr(_instance, 'getDetails')):
            _instance.addCleanup(_detail.gather_details,
                                 fixture.getDetails(),
                                 _instance.getDetails())
        return fixture
