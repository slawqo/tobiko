from __future__ import absolute_import

from oslo_log import log
import pandas
import six

import tobiko
from tobiko.tripleo import overcloud
from tobiko.shell import sh


LOG = log.getLogger(__name__)


class OvercloudServiceException(tobiko.TobikoException):
    message = "not all overcloud nodes services are in active state"


def get_overcloud_node_services_table(hostname):
    """
    get services table from overcloud node

       returns :
auditd.service|loaded|active|running|SecurityAuditingService
auth-rpcgss-module.service|loaded|inactivedead|KernelModulesupportingRPCSEC_GSS
blk-availability.service|loaded|active|exited|Availabilityofblockdevices
brandbot.service|loaded|inactivedead|FlexibleBrandingService
certmonger.service|loaded|active|running|CertificatemonitoringandPKIenrollment
cinder-lvm-losetup.service|loaded|inactivedead|CinderLVMlosetup
cloud-config.service|loaded|active|exited|Applythesettingsspecifiedincloud-con
cloud-final.service|loaded|active|exited|Executeclouduser/finalscripts
cloud-init-local.service|loaded|active|exited|Initialcloud-initjob(pre-network)
cloud-init.service|loaded|active|exited|Initialcloud-initjob(metadataservicecr)

    :return: dataframe of overcloud node services
    """

    ssh_client = overcloud.overcloud_ssh_client(hostname)
    output = sh.execute(
        "systemctl -a --no-pager --plain --no-legend|grep -v not-found|"
        "sed \'s/\\s\\s/|/g\'|sed \'s/||*/DELIM/g\'|sed \'s@ @@g\'|"
        "sed \'s/DELIM$//g\'",
        ssh_client=ssh_client).stdout
    stream = six.StringIO(output)
    table = pandas.read_csv(stream, sep='DELIM', header=None, skiprows=0)
    table.replace(to_replace=' ', value="", regex=True, inplace=True)
    table.columns = ['UNIT', 'loaded_state', 'active_state',
                     'low_level_state', 'UNIT_DESCRIPTION']
    table['overcloud_node'] = hostname

    LOG.debug("Got overcloud nodes services status :\n%s", table)
    return table


def get_overcloud_nodes_running_service(service):
    """
    Check what nodes are running the specified service or unit
    process: exact str of a process name as seen in systemctl -a
    :return: list of overcloud nodes
    """
    oc_procs_df = overcloud.get_overcloud_nodes_dataframe(
                                            get_overcloud_node_services_table)
    oc_nodes_running_service = oc_procs_df.query('UNIT=="{}"'.format(service))[
                                                'overcloud_node'].unique()
    return oc_nodes_running_service


def check_if_process_running_on_overcloud(process):
    """
    Check what nodes are running the specifies
    process: exact str of a process name as seen in ps -axw -o "%c"
    :return: list of overcloud nodes
    """
    oc_services_df = overcloud.get_overcloud_nodes_dataframe(
                                            get_overcloud_node_services_table)
    if not oc_services_df.query('UNIT=="{}"'.format(process)).empty:
        return True
    else:
        return False


class OvercloudServicesStatus(object):
    """
    class to handle services checks,
    checks that all of these are running in the overcloud:
    'corosync.service','iptables.service','network.service','ntpd.service',
    'pacemaker.service','rpcbind.service','sshd.service'

    """
    def __init__(self):
        self.services_to_check = ['corosync.service', 'iptables.service',
                                  'network.service', 'ntpd.service',
                                  'pacemaker.service', 'rpcbind.service',
                                  'sshd.service']

        self.oc_services_df = overcloud.get_overcloud_nodes_dataframe(
                                            get_overcloud_node_services_table)

    @property
    def basic_overcloud_services_running(self):
        """
        Checks that the oc_services dataframe has all of the list services
        running
        :return: Bool
        """
        for service_name in self.services_to_check:
            if not self.oc_services_df.query('UNIT=="{}"'.format(
                    service_name)).empty:
                LOG.info("overcloud processes status checks: process {} is  "
                         "in running state".format(service_name))
                continue
            else:
                LOG.info("Failure : overcloud processes status checks: "
                         "process {} is not running ".format(service_name))
                raise OvercloudServiceException()
        return True
