from __future__ import absolute_import

import testtools


from tobiko.tests.faults.ha import cloud_disruptions
from tobiko.tripleo import pacemaker
from tobiko.tripleo import undercloud


@undercloud.skip_if_missing_undercloud
class DisruptTripleoInstanceHaTest(testtools.TestCase):

    @pacemaker.skip_if_instanceha_not_delpoyed
    def test_instanceha_evacuation_hard_reset(self):
        cloud_disruptions.check_iha_evacuation_hard_reset()

    @pacemaker.skip_if_instanceha_not_delpoyed
    def test_instanceha_evacuation_network_disruption(self):
        cloud_disruptions.check_iha_evacuation_network_disruption()

    @pacemaker.skip_if_instanceha_not_delpoyed
    def test_instanceha_evacuation_hard_reset_shutoff_instance(self):
        cloud_disruptions.check_iha_evacuation_hard_reset_shutoff_instance()

    # @pacemaker.skip_if_instanceha_not_delpoyed
    # def test_check_instanceha_evacuation_evac_image_vm(self):
    #     overcloud_health_checks(passive_checks_only=True)
    #     cloud_disruptions.check_iha_evacuation_evac_image_vm()
