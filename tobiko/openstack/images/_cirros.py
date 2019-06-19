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


from tobiko import config
from tobiko.openstack import glance

CONF = config.CONF


class CirrosImageFixture(glance.GlanceImageFixture):

    @property
    def image(self):
        """glance image used to create a Nova server instance"""
        return CONF.tobiko.nova.image

    @property
    def username(self):
        """username used to login to a Nova server instance"""
        return CONF.tobiko.nova.username

    @property
    def password(self):
        """password used to login to a Nova server instance"""
        return CONF.tobiko.nova.password

    def create_image(self):
        raise NotImplementedError
