.. _tobiko-contributor-guide:

========================
Tobiko Contributor Guide
========================


Document Overview
-----------------

This document describes how to configure a developer workstation
to run Tobiko test cases against a remote OpenStack cloud

.. sidebar:: See also

    To just execute Tobiko test cases pelase read
    :ref:`tobiko-quick-start-guide`.

    To install Tobiko inside a virutalenv please read
    :ref:`tobiko-installation-guide`.

    To configure Tobiko please read :ref:`tobiko-configuration-guide`.

    To run Tobiko scenario test cases please look at
    :ref:`tobiko-test-case-execution-guide`.


This tutorial will guide you to configure a developer workstation to be able
to run Tobiko test cases locally without requiring direct network
connectivity to a remote OpenStack cloud (DevStack based or TripleO based) so
that the edit-try-debug cycle should get shorter and simpler than by
editing test cases on one host that is not the same where test cases are being
executed::

    [ test cases host ] - SSH -> [SSH proxy host] - IP -> [OpenStack cloud]


Install Dependencies
--------------------

Install Basic Python Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure Git and Python 3 are installed on your system.

For instance on RedHat Linux / Fedora::

    sudo dnf install -y git python3 which

Check your Python 3 version is 3.6 or greater::

    python3 --version

Make sure pip is installed and up-to date::

    curl https://bootstrap.pypa.io/get-pip.py | sudo python3

Check installed Pip version::

    python3 -m pip --version

Make sure basic Python packages are installed and up-to-date::

    sudo python3 -m pip install --upgrade setuptools wheel virtualenv tox six

Check installed Tox version::

    tox --version


Clone the Tobiko repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clone the Tobiko repository using Git::

    git clone https://opendev.org/x/tobiko.git
    cd tobiko


Install Missing Binary Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install required binary packages::

    tools/install-bindeps.sh


Configure Logging Options
-------------------------

Test cases load most of the configuration parameters from an INI configuration file,
typically found at one of the following locations:

- ./tobiko.conf (Tobiko source files directory)
- ~/.tobiko/tobiko.conf
- /etc/tobiko/tobiko.conf

Create it in the Tobiko source directory with the following (or as your preferences). Example::

    [DEFAULT]
    debug = true
    log_file = tobiko.log


The file 'tobiko.log' is the default file where test cases and the Python framework
are going to write their logging messages. By setting debug as 'true' you
ensure that messages with the lowest logging level are written there (DEBUG level).
The log_file location specified above is relative to the tobiko.conf file
location. In this example it is the Tobiko source files directory itself
because in case of a relative path the directory where the tobiko.conf file
is used as current directory.


SetUp SSH public key to connect to remote cloud
-----------------------------------------------

Tobiko test cases will be able to setup some type of SSH tunneling
to be able to reach the remote cloud, but for archiving it you are
required to be able to connect to a remote SSH server that is
able to connect to the OpenStack services and hosts. We will
call that server here as the SSH proxy host.

Tobiko test cases will execute some commands on the SSH proxy host
(like ping, nc, curl, etc.) as soon as these command need to
have direct connectivity to target cloud.

Test case will use Python REST API clients configured to make HTTP
requests coming out from such SSH server (mainly by using nc
command) or SSH server direct connect feature.

Test cases will make all SSH connection to cloud nodes by using
this SSH proxy host

To resume the purpose of the SSH proxy, all network packages
sent by Tobiko test cases to the tested cloud will come from the
SSH proxy host, while all Tobiko test cases will be executed
from the developer workstation.

In order to archive it, first of all we need to make sure we can
connect to the SSH proxy server without requiring any password.
We therefore need to have a local SSH key pair to be used by tobiko.
This key by default is the same default one used by openSSH client:
- default SSH private key filename:  `~/.ssh/id_rsa`
- default SSH public key filename:  `~/.ssh/id_rsa.pub`
To avoid having problems with other uses of the same file, lets instead
create our SSH key pair only for Tobiko in a sub-folder near to
your tobiko.conf

Ensure we do have this key pair on your workstation by typing::

    mkdir -p .ssh
    chmod 700 .ssh
    ssh-keygen -v -f .ssh/id -N ''
    chmod 600 .ssh/id .ssh/id.pub


Please note in case you already have this pair of files created before
that, the key pair must have an empty passphrase. That means the SSH client
will never ask you a password to connect to a remote server using that
key pair.

Define below variables to later connect to your SSH server::

    SSH_HOST=<your-ssh-proxy-address>
    SSH_USERNAME=<your-ssh-proxy-user>


Ensure you can connect to the remote SSH server using
our new key pair without a password::

    ssh-copy-id -i .ssh/id "${SSH_USERNAME}@${SSH_HOST}"


Check the SSH key pair is working::

    ssh -i .ssh/id "${SSH_USERNAME}@${SSH_HOST}" hostname


Create '.ssh/config' file with SSH proxy connection parameters::

    echo "
    Host ssh-proxy ${SSH_HOST}
        IdentityFile .ssh/id
        IdentitiesOnly yes
        HostName ${SSH_HOST}
        User ${SSH_USERNAME}
        StrictHostKeyChecking no
        PasswordAuthentication no
        UserKnownHostsFile /dev/null
    " > .ssh/config
    chmod 600 .ssh/config


Check the SSH config file is working::

    ssh -F .ssh/config ssh-proxy hostname


Now let tell Tobiko test cases to use these SSH key pair and to connect
to your SSH remote host by editing tobiko.conf file::

    [ssh]
    proxy_jump = ssh-proxy
    config_files = .ssh/config


We also want to tell Tobiko to use the same key pair to connect to VMs
created by Tobiko test cases::

    [nova]
    key_file = .ssh/id


Configure Tobiko Credentials
----------------------------

In order to run the OpenStack test cases Tobiko needs to have Keystone credentials.
To make our life simpler we are going to assume you are using one of the two
OpenStack distributions supported by Tobiko:

- DevStack
- TripleO

Get credentials from a DevStack host
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get the clouds.yaml file from a remote DevStack host::

    ssh <... connection options here ...> cat /etc/openstack/clouds.yaml > clouds.yanl


If your SSH proxy host configured before is one of your DevStack cloud hosts
then you can type::

    ssh -F .ssh/config ssh-proxy cat /etc/openstack/clouds.yaml > clouds.yaml


Edit your tobiko.conf file to pick your DevStack based cloud::

    [keystone]
    cloud_name = devstack-admin
    clouds_file_names = clouds.yaml


Get credentials from TripleO undercloud host
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First of all let discover undercloud host IP by pinging it from ssh-proxy host::

    UNDERCLOUD_IP=$(
        ssh -F .ssh/config ssh-proxy ping -c 1 undercloud-0 |
        awk '/^PING/{gsub(/\(|\)/,""); print $3}')
    echo $UNDERCLOUD_IP


Tobiko should be able to get credentials directly from such undercloud node but it
must know the address of the undercloud host, so we must edit tobiko.conf to
let it know::

     [tripleo]
     undercloud_ssh_hostname=<undercloud-host-address>


Run Tobiko test cases
---------------------

Running Scenario Test Cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To see if we are now able to execute Tobiko test cases please keep open a new
terminal where to watch tobiko.log file on the same folder of tobiko.conf file::

    tail -F tobiko.log

Then in the first terminal execute some Tobiko test cases as below::

    tox -v -e scenario -- -v tobiko/tests/scenario/neutron/test_floating_ip.py::FloatingIPTest


Scenario test cases are used to create workloads that simulate real-world use
of OpenStack. They create networks, virtual machines, ports, routers, etc.
They also test validate that these workloads functioning.

Running Tobiko scenario test cases using Tox (may take several minutes to complete)::

    tox -e scenario


Listing Tobiko Workloads
------------------------

To manage workloads created by Tobiko please log to remote cloud node

Listing Tobiko Workloads on DevStack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To list workloads generated by tobiko you can use glance and heat CLI from
the SSH proxy host node::

    ssh -i .ssh/config ssh-proxy
    export OS_CLOUD=devstack-amdin
    openstack image list
    openstack stack list


Listing Tobiko Workloads on DevStack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To list workloads generated by tobiko you can use glance and heat CLI from
the undercloud-0 host node::

    ssh -F .ssh/config ssh-proxy -t ssh stack@undercloud-0
    source overcloudrc
    openstack image list
    openstack stack list


Verify Tobiko Workloads
-----------------------

Scenario test cases are also used to check that previously created resources are
still up and working as expected. To ensure test cases will not create those
resources again we can set `TOBIKO_PREVENT_CREATE` environment variable before
re-running test cases::

    TOBIKO_PREVENT_CREATE=yes tox -e scenario -- -v tobiko/tests/scenario/neutron/test_floating_ip.py::FloatingIPTest


Cleaning Up Tobiko Workloads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once Tobiko test cases have been executed, we may want to clean up all
workloads remaining on the cloud so that we restore it to its original state.

Cleaning Up Heat Stacks
++++++++++++++++++++++++

Because Tobiko is using Heat stacks for orchestrating the creation of most of
the resources, deleting all stacks created with Tobiko will clean up
almost all resources::

    openstack stack list -f value -c ID | xargs openstack stack delete


Cleaning Up Glance Images
++++++++++++++++++++++++++

Because Heat doesn't support creation of Glance images, Tobiko implements some
specific fixtures to download images from the Web and upload them to the Glance
service::

    openstack image list -f value -c ID | xargs openstack image delete


Running Disruptive Test Cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Disruptive test cases are used for testing that after inducing some critical
disruption to the operation of the cloud, the services return working as expected after
a while. To execute them you can type::

    tox -e faults

The faults induced by these test cases could be cloud nodes reboot,
OpenStack services restart, virtual machines migrations, etc.

Please note that while scenario test cases are being executed in parallel (to
speed up test case execution), disruptive test case are only executed sequentially.
This is because the operations executed by such cases could break some functionality
for a short time and alter the regular state of the system which may be assumed by other
test cases to be executed.


Running the Tobiko Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Scenario and disruptive test cases, being executed in a specific sequence could
be used to uncover more issues with the cloud than disruptive test cases alone.

- First ensure there are workloads properly running by running scenario test cases::

    tox -e scenario

.. sidebar:: Note

    As second step we may, instead, update or upgrade OpenStack nodes.

- Next we could execute disruptive test cases to "stress" the cloud::

    tox -e faults

- Finally we might re-run scenario test cases to check that everything is still running
  as expected::

    TOBIKO_PREVENT_CREATE=yes tox -e scenario
