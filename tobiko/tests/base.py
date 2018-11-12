# Copyright (c) 2018 Red Hat
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
from tempest import config
import testscenarios
import testtools

from tobiko.common import constants
from tobiko.common import clients


class TobikoTest(testtools.testcase.WithAttributes,
                 testscenarios.WithScenarios,
                 testtools.TestCase):

    def setUp(self):
        super(TobikoTest, self).setUp()
        self.conf = config.CONF
        self.default_params = {
            'public_net': self.conf.network.floating_network_name,
            'image': self.conf.compute.image_ref,
            'flavor': constants.DEFAULT_FLAVOR}
        self.clientManager = clients.ClientManager(conf=self.conf)
