from __future__ import absolute_import

import tobiko

from tobiko.shell import ssh


def undercloud_ssh_client():
    host_config = undercloud_host_config()
    return ssh.ssh_client(host='undercloud-0', host_config=host_config)


def undercloud_host_config():
    return tobiko.setup_fixture(UndecloudHostConfig)


def has_undercloud():
    host_config = undercloud_host_config()
    return bool(host_config.hostname)


skip_if_missing_undercloud = tobiko.skip_unless(
    'TripleO Undercloud hostname is not configured',
    has_undercloud)


class UndecloudHostConfig(tobiko.SharedFixture):

    host = 'undercloud-0'
    hostname = None
    port = None
    username = None
    key_filename = None

    def setup_fixture(self):
        from tobiko import config
        conf = config.CONF.tobiko.tripleo
        self.hostname = conf.undercloud_ssh_hostname
        self.port = conf.undercloud_ssh_port
        self.username = conf.undercloud_ssh_username
        self.key_filename = conf.ssh_key_filename
