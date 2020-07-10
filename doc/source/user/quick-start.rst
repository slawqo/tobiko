.. _tobiko-quick-start-guide:

========================
Tobiko Quick Start Guide
========================


Document Overview
-----------------

This document describes how to install execute Tobiko test cases
using `Tox <https://tox.readthedocs.io/en/latest/>`__.

.. sidebar:: See also

    To install Tobiko inside a virutalenv please read
    :ref:`tobiko-installation-guide`.

    To configure Tobiko please read :ref:`tobiko-configuration-guide`.

    To run Tobiko scenario test cases please look at
    :ref:`tobiko-test-case-execution-guide`.


Install Dependencies
--------------------

Install Basic Python Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure Git and Python 3 are installed on your system.

For instance on RedHat Linux / Fedora::

    sudo yum install -y git python3 which

Check your Python 3 version is greater than 3.6::

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
    debug = True
    log_file = tobiko.log

The file 'tobiko.log' is the default file where test cases and the Python framework
are going to write their logging messages. By setting debug as 'true' you
ensure that messages with the lowest logging level are written there (DEBUG level).
The log_file location specified above is relative to the tobiko.conf file
location. In this example it is the Tobiko source files' directory itself.


Configure Tobiko Credentials
----------------------------

In order to run the OpenStack test cases you'll need to set up Keystone
credentials. You can do it in one of following ways:

- :ref:`credentials-from-clouds-file`
- :ref:`credentials-from-env`
- :ref:`credentials-from-config`


.. _credentials-from-clouds-file:


Set Tobiko Credentials from clouds.yaml file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure that in any one of below locations there is a valid
`OpenStack clouds file <https://docs.openstack.org/python-openstackclient/pike/configuration/index.html#clouds-yaml>`__
containing valid Keystone credentials:

  - Tobiko source files directory
  - ~/.config/openstack
  - /etc/openstack


Finally, you will need to specify which credentials Tobiko should pick up via
'OS_CLOUD' environment variable or by specifying the cloud_name in tobiko.conf file
(section 'keystone', option 'cloud_name').


Specify 'OS_CLOUD' environment variable
+++++++++++++++++++++++++++++++++++++++

Ensure *OS_CLOUD* environment variable is defined before executing Tobiko test
cases::

    export OS_CLOUD=<cloud_name>


Please choose a valid cloud_name from your clouds.yaml file.


Specify cloud_name in tobiko.conf file
++++++++++++++++++++++++++++++++++++++


Create file `tobiko.conf` in Tobiko sources folder adding a section like below::

    [keystone]
    cloud_name = <cloud_name>


Please choose a valid cloud_name from your clouds.yaml file.


.. _credentials-from-env:


Set Tobiko Credentials Via Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. sidebar:: See also

    For more details about supported environment variables please read
    :ref:`authentication-environment-variables` section.

You can use an existing shell RC file that is valid for
`Python OpenStack client <https://docs.openstack.org/python-openstackclient/latest/cli/man/openstack.html#environment-variables>`__
::

    source openstackrc

An example of 'openstackrc' file could looks like below::

    export OS_IDENTITY_API_VERSION=3
    export OS_AUTH_URL=https://my_cloud:13000/v3
    export OS_USERNAME=admin
    export OS_PASSWORD=secret
    export OS_PROJECT_NAME=admin
    export OS_USER_DOMAIN_NAME=Default
    export OS_PROJECT_DOMAIN_NAME=Default


.. _credentials-from-config:

Set Tobiko Credentials Via :ref:`tobiko-conf` File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. sidebar:: See also

    For more details about supported configuration options please read
    :ref:`authentication-configuration` section.

Create a file at `~/.tobiko/tobiko.conf` and add a section as in the
example below (Or add to your existing file)::

    [keystone]
    api_version = 3
    auth_url = http://my_cloud:13000/v3
    username = admin
    password = secret
    project_name = admin
    user_domain_name = Default
    project_domain_name = Default


Setup Required Resources
~~~~~~~~~~~~~~~~~~~~~~~~

A public Neutron network is required To be able to execute Tobiko scenario test
cases by creating a floating IP port on it.

To execute commands from a virtualenv created by Tox you can type as below::

    tox -e venv -- <your-commands>

You need to make sure ref:`authentication-environment-variables` are properly
set so you can list available public netoworks::

    tox -e venv -- openstack network list

If there is any valid public network, you need to create one before running
Tobiko OpenStack test cases. Please refer to the `Neutron documentation <https://docs.openstack.org/neutron/latest/>`__
for additional information.


If there is a valid public network for creating floating-IP ports on,
Tobiko tests cases will automatically use it. To explicitly select a network,
please add a reference to the network in
:ref:`tobiko-conf` file::

    [neutron]
    floating_network = public


Running Test Cases
------------------

Running Scenario Test Cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Scenario test cases are used to create workloads that simulate real-world use
of OpenStack. They create networks, virtual machines, ports, routers, etc.
They also test validate that these workloads functioning.

Running Tobiko scenario test cases using Tox (may take some time to complete (minutes))::

    tox -e scenario

To list Heat stacks and Glance images created by test cases::

    tox -e venv -- openstack image list
    tox -e venv -- openstack stack list

Scenario test cases are also used to check that previously created resources are
still up and working as expected. To ensure test cases will not create those
resources again we can set `TOBIKO_PREVENT_CREATE` environment variable before
re-running test cases::

  TOBIKO_PREVENT_CREATE=yes tox -e scenario


Cleanning Up Tobiko Workloads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once Tobiko test cases have been executed, we may want to clean up all
workloads remaining on the cloud so that we restore it to its original state.


Cleanning Up Heat Stacks
++++++++++++++++++++++++

Because Tobiko is using Heat stacks for orchestrating the creation of most of
the resources, deleting all stacks created with Tobiko will clean up
almost all resources::

  tox -e venv -- bash -c 'openstack stack list -f value -c ID | xargs openstack stack delete'


Cleanning Up Glance Images
++++++++++++++++++++++++++

Because Heat doen't support creation of Glance images, Tobiko implemented some
specific fixtures to download images from the Web and upload them to the Glance
service::

    tox -e venv -- bash -c 'openstack image list -f value -c ID | xargs openstack image delete'


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

- Finally we might re-run scenario test cases to check thateverything is still running
  as expected::

    TOBIKO_PREVENT_CREATE=yes tox -e scenario


Test Cases Report Files
~~~~~~~~~~~~~~~~~~~~~~~

After executing test cases we can view the results in greater detail via a small
set of files:

  - **test_results.html**:
    A user-browseable HTML view of test case results
  - **test_results.log**:
    a log file with logging traces collected from every individual test case
  - **test_results.subunit**:
    the original subunit binary file generated by test runner
  - **test_results.xml**:
    an XML Junit file to be used, for example, to show test cases result by
    Jenkins CI server

The names of the above files can be changed from the default value (*test_results*)
to a custom one by setting the *TOX_REPORT_NAME* environment variable.

.. sidebar:: Legend

    *{toxinidir}* stand for the Tobiko source files directory.

    *{envname}* is the name of the Tox enviroment to be executed (IE scenario,
    faults, etc.)

The above files are saved into a folder that can be specified with
*TOX_REPORT_DIR* environment variable.

By default the full path of the report directory is made from the below::

    {toxinidir}/report/{envname}
