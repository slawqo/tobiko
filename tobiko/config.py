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

import importlib
import os

from oslo_config import cfg
from oslo_log import log

CONFIG_MODULES = ['oslo_log.log',
                  'tobiko.tests.config']

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

    def __setattr__(self, name, conf):
        if conf is None:
            raise TypeError("Config source cannot be None")
        actual = self._sources.setdefault(name, conf)
        if actual is not conf:
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
    init_tempest_config()
    init_environ_config()


def init_tobiko_config(default_config_dirs=CONFIG_DIRS, product_name='tobiko',
                       version='unknown'):
    conf = cfg.ConfigOpts()
    register_options(conf=conf)
    conf(args=[], default_config_dirs=default_config_dirs)
    setup(conf=conf, product_name=product_name, version=version)
    CONF.tobiko = conf


def register_options(conf):
    for module_name in CONFIG_MODULES:
        module = importlib.import_module(module_name)
        register_options_func = getattr(module, 'register_options', None)
        if register_options_func:
            register_options_func(conf=conf)

    def dummy_log_register_options(conf):
        pass
    log.register_options = dummy_log_register_options


def setup(conf, product_name, version):
    for module in CONFIG_MODULES:
        setup_func = getattr(module, 'setup', None)
        if setup_func:
            setup_func(conf=conf, product_name=product_name, version=version)

    def dummy_log_setup(conf, product_name, version=None):
        pass
    log.setup = dummy_log_setup


def init_tempest_config():
    try:
        from tempest import config
    except ImportError:
        pass
    else:
        CONF.tempest = tempest_conf = config.CONF
        if 'http_proxy' not in os.environ or 'https_proxy' not in os.environ:
            if tempest_conf.service_clients.proxy_url:
                os.environ['http_proxy'] = (
                    tempest_conf.service_clients.proxy_url)


def init_environ_config():
    CONF.environ = EnvironConfig()


class EnvironConfig(object):

    def __getattr__(self, name):
        try:
            os.environ[name]
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
