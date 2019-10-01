# Copyright 2019 Red Hat
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

import os

import jinja2

from oslo_log import log

import tobiko
from tobiko.tripleo import overcloud
from tobiko.shell import ssh


LOG = log.getLogger(__name__)


def get_os_fault_config_filename():
    return tobiko.setup_fixture(OsFaultsConfigFileFixture).config_filename


class OsFaultsConfigFileFixture(tobiko.SharedFixture):
    """Responsible for managing faults configuration."""

    config = None
    config_filename = None
    template_filename = None

    def __init__(self, config=None, config_filename=None,
                 template_filename=None):
        super(OsFaultsConfigFileFixture, self).__init__()
        self.templates_dir = os.path.join(os.path.dirname(__file__),
                                          'templates')
        if config is not None:
            config = config
        if config_filename is not None:
            self.config_filename = config_filename
        if template_filename is not None:
            self.template_filename = template_filename

    def setup_fixture(self):
        _config = self.config
        if not _config:
            from tobiko import config
            CONF = config.CONF
            self.config = _config = CONF.tobiko.os_faults
        self.config_filename = config_filename = self.get_config_filename()
        if config_filename is None:
            self.config_filename = self.generate_config_file(
                config_filename=config_filename)

    def get_config_filename(self):
        config_filename = self.config_filename
        if config_filename is None:
            config_filename = os.environ.get('OS_FAULTS_CONFIG') or None

        if config_filename is None:
            config_dirnames = self.config.config_dirnames
            config_filenames = self.config.config_filenames
            for dirname in config_dirnames:
                dirname = os.path.realpath(os.path.expanduser(dirname))
                for filename in config_filenames:
                    filename = os.path.join(dirname, filename)
                    if os.path.isfile(filename):
                        config_filename = filename
                        break

        if config_filename is None:
            LOG.warning("Unable to find any of 'os_faults' files (%s) in "
                        "any directory (%s",
                        ', '.join(config_filenames),
                        ', '.join(config_dirnames))
        return config_filename

    def get_template_filename(self):
        template_filename = self.template_filename
        if template_filename is None:
            template_filename = os.environ.get('OS_FAULTS_TEMPLATE') or None

        if template_filename is None:
            template_dirnames = self.config.template_dirnames
            config_filenames = self.config.config_filenames
            template_filenames = [filename + '.j2'
                                  for filename in config_filenames]
            for dirname in template_dirnames:
                dirname = os.path.realpath(os.path.expanduser(dirname))
                for filename in template_filenames:
                    filename = os.path.join(dirname, filename)
                    if os.path.isfile(filename):
                        template_filename = filename
                        break

        if template_filename is None:
            LOG.warning("Unable to find any of 'os_faults' template file "
                        "(%s) in any directory (%s").format(
                            ', '.join(template_filenames),
                            ', '.join(template_dirnames))
        return template_filename

    def generate_config_file(self, config_filename):
        """Generates os-faults configuration file."""

        self.template_filename = template_filename = (
            self.get_template_filename())
        template_basename = os.path.basename(template_filename)
        if config_filename is None:
            config_dirname = os.path.realpath(
                os.path.expanduser(self.config.generate_config_dirname))
            config_basename, template_ext = os.path.splitext(template_basename)
            assert template_ext == '.j2'
            config_filename = os.path.join(config_dirname, config_basename)
        else:
            config_dirname = os.path.dirname(config_filename)

        LOG.info("Generating os-fault config file from template %r to %r.",
                 template_filename, config_filename)
        tobiko.makedirs(config_dirname)

        template_dirname = os.path.dirname(template_filename)
        j2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dirname),
            trim_blocks=True)
        template = j2_env.get_template(template_basename)
        config_content = template.render(
            nodes=self.list_nodes(),
            services=self.list_services(),
            containers=self.list_containers())
        with tobiko.open_output_file(config_filename) as f:
            f.write(config_content)
        return config_filename

    def list_services(self):
        return self.config.services

    def list_containers(self):
        return self.config.containers

    def list_nodes(self):
        """Returns a list of dictionaries with nodes name and address."""
        nodes = self.config.nodes
        if nodes:
            return [parse_config_node(node_string)
                    for node_string in nodes]
        elif overcloud.has_overcloud():
            nodes = []
            overcloud_nodes = overcloud.list_overcloud_nodes()
            for overcloud_node in overcloud_nodes:
                overcloud_host_config = overcloud.overcloud_host_config(
                    overcloud_node.name)
                address = str(overcloud_host_config.hostname)
                os_faults_node = dict(
                    name=overcloud_node.name,
                    address=address,
                    username=overcloud_host_config.username,
                    private_key_file=overcloud_host_config.key_filename)
                host_config = ssh.ssh_host_config(host=address)
                if host_config.proxy_jump:
                    proxy_config = ssh.ssh_host_config(
                        host=host_config.proxy_jump)
                    os_faults_node['jump'] = dict(
                        username=proxy_config.username,
                        host=proxy_config.hostname,
                        private_key_file=os.path.expanduser(
                            proxy_config.key_filename))
                nodes.append(os_faults_node)
            return nodes

        raise NotImplementedError("Cloud node listing not configured.")


def parse_config_node(node):
    fields = node.split('.')
    if len(fields) != 2:
        message = ("Invalid cloud node format: {!r} "
                   "(expected '<name>:<address>')").format(node)
        raise ValueError(message)
    return {'name': fields[0],
            'address': fields[1]}
