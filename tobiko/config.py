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

import importlib
import os

from oslo_config import cfg
from oslo_log import log

LOG = log.getLogger(__name__)

CONFIG_MODULES = ['tobiko.tests.config']

CONFIG_DIRS = [os.getcwd(),
               os.path.expanduser("~/.tobiko"),
               '/etc/tobiko']


class GlobalConfig(object):

    # this is a singletone
    _instance = None
    _sources = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def set_source(self, name, source_conf):
        if source_conf is None:
            raise TypeError("Config source cannot be None")
        actual = self._sources.setdefault(name, source_conf)
        if actual is not source_conf:
            msg = "Config source already registered: {!r}".format(name)
            raise RuntimeError(msg)

    def __getattr__(self, name):
        sources = self._sources.get(name)
        if sources is None:
            msg = "Config source not registered: {!r}".format(name)
            raise NoSuchConfigSource(msg)
        return sources


CONF = GlobalConfig()


def init_config():
    init_tobiko_config()
    init_environ_config()
    if CONF.tobiko.tempest.enabled:
        init_tempest_config()


def init_tobiko_config(default_config_dirs=None, product_name='tobiko',
                       version='unknown'):
    default_config_dirs = default_config_dirs or CONFIG_DIRS

    # Register configuration options
    conf = cfg.ConfigOpts()
    log.register_options(conf)
    register_tobiko_options(conf=conf)

    # Initialize tobiko configuration object
    conf(args=[], default_config_dirs=default_config_dirs)
    CONF.set_source('tobiko', conf)

    # setup final configuration
    log.setup(conf=conf, product_name=product_name, version=version)
    setup_tobiko_config()


def register_tobiko_options(conf):
    conf.register_opts(
        group=cfg.OptGroup('tempest'),
        opts=[cfg.BoolOpt('enabled',
                          default=True,
                          help="Enables tempest integration if available"),
              ])

    for module_name in CONFIG_MODULES:
        module = importlib.import_module(module_name)
        if hasattr(module, 'register_tobiko_options'):
            module.register_tobiko_options(conf=conf)


def setup_tobiko_config():
    for module_name in CONFIG_MODULES:
        module = importlib.import_module(module_name)
        if hasattr(module, 'setup_tobiko_config'):
            module.setup_tobiko_config()


def init_tempest_config():
    try:
        from tempest import config

        # checks tempest configuration is working
        tempest_conf = config.CONF
        tempest_logger = log.getLogger('tempest')
        if tempest_conf.debug:
            # Silence tempest logger
            if not tempest_logger.isEnabledFor(log.DEBUG):
                tempest_logger.logger.setLevel(log.DEBUG)
        else:
            # Silence tempest logger
            if tempest_logger.isEnabledFor(log.INFO):
                tempest_logger.logger.setLevel(log.WARNING)

    except Exception:
        LOG.exception('Errors configuring tempest integration')

    else:
        CONF.set_source('tempest', tempest_conf)


def init_environ_config():
    CONF.set_source('environ', EnvironConfig())


class EnvironConfig(object):

    def __getattr__(self, name):
        try:
            return os.environ[name]
        except KeyError:
            msg = "Environment variable not found: {!r}".format(name)
            raise cfg.NoSuchOptError(msg)


class NoSuchConfigSource(AttributeError):
    pass


def get_any_option(*sources, **kwargs):
    default = kwargs.get('default', None)
    for source in sources:
        value = CONF
        for name in source.split('.'):
            try:
                value = getattr(value, name)
            except (NoSuchConfigSource,
                    cfg.NoSuchOptError,
                    cfg.NoSuchGroupError):
                break

        else:
            if value != default:
                return value
    return default


init_config()
