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

For instance on RedHat Linux you could type::

    sudo yum install -y git python3

Check your Python 3 version is greater than 3.6::

    python3 --version

Make sure Pip is installed and up-to date::

    curl https://bootstrap.pypa.io/get-pip.py | sudo python3

Check installed Pip version::

    python3 -m pip --version

Make sure basic Python packages are installed and up-to-date::

    sudo python3 -m pip install --upgrade setuptools wheel virtualenv tox six

Check installed Tox version::

    tox --version


Get Tobiko Source Code
~~~~~~~~~~~~~~~~~~~~~~

Get Tobiko source code using Git::

    git clone https://opendev.org/x/tobiko.git
    cd tobiko


Install Missing Binary Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check required binary packages are installed::

    tox -e bindep

For instance on a clean CentOS 8 host at this point I could expect to get below
errors::

    Missing packages:
        bzip2-devel libffi-devel openssl-devel python3-devel python3-wheel readline-devel sqlite-devel
    ERROR: InvocationError for command /home/vagrant/tobiko/.tox/bindep/bin/bindep test (exited with code 1)

Fix above error by simply installing missing packages::

    .tox/bindep/bin/bindep -b | xargs -r sudo yum install -y

Finally check again all missing packages are installed::

    $ tox -e bindep
    bindep installed: bindep==2.8.1,distro==1.5.0,Parsley==1.3,pbr==5.4.5
    bindep run-test-pre: PYTHONHASHSEED='1750048501'
    bindep run-test: commands[0] | bindep test
    __________________________________________________________________________ summary __________________________________________________________________________
      bindep: commands succeeded
      congratulations :)


Configure Logging Options
-------------------------

Test cases load most of configurations parameters from a INI configuration file
typically found at one of below locations:

    - ./tobiko.conf (Tobiko source files directory)
    - ~/.tobiko/tobiko.conf
    - /etc/tobiko/tobiko.conf

Create it in Tobiko source directory with your very basic preferences. Example::

    [DEFAULT]
    debug = True
    log_file = tobiko.log

File 'tobiko.log' is the default file where test cases and the Python framework
are going to write their logging messages. By setting debug as 'true' you
ensures messages with the lowest logging level are written there (DEBUG level).
The log_file location specified above is relative to the tobiko.conf file
location, thats mean on this case the Tobiko source files directory itself.


Configure Tobiko Credentials
----------------------------

In order to run the OpenStack test cases you'll need to set up KeyStone
credentials. You can do it in one of below ways:

- :ref:`credentials-from-clouds-file`
- :ref:`credentials-from-env`
- :ref:`credentials-from-config`


.. _credentials-from-clouds-file:


Set Tobiko Credentials from clouds.yaml file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure in any of below locations there is a valid
`OpenStack clouds file <https://docs.openstack.org/python-openstackclient/pike/configuration/index.html#clouds-yaml>`__
containing valid KeyStone credentials:

  - Tobiko source files directory
  - ~/.config/openstack
  - /etc/openstack


Finally you need to specify which credentials Tobiko should pick up via
'OS_CLOUD' environment variable or by specifying cloud name in tobiko.conf file
(section 'keystone', option 'cloud_name').


Specify 'OS_CLOUD' environment variable
+++++++++++++++++++++++++++++++++++++++

Ensure below environment variable is defined before executing Tobiko test
cases::

    export OS_CLOUD=<cloud-name>


Please chose a valid cloud name from your clouds.yaml file.


Specify cloud name in tobiko.conf file
++++++++++++++++++++++++++++++++++++++


Create file `tobiko.conf` in Tobiko sources folder adding a section like below::

    [keystone]
    cloud_name = <cloud-name>


Please chose a valid cloud name from your clouds.yaml file.


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

Create a file at `~/.tobiko/tobiko.conf` adding a section like below::

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
cases to be able to create floating IP port on it.

To execute commands from a virtualenv created by Tox you can type as below::

    tox -e venv -- <your-commands>

You need to make sure ref:`authentication-environment-variables` are properly
set so you can list available public netoworks::

    tox -e venv -- openstack network list

If there is any valid public network you need to create one before running
Tobiko OpenStack test cases. Please refer to the
`Neutron documentation <https://docs.openstack.org/neutron/latest/>` to know
how to do it.


If there is a valid public network for creating floating IPs ports on it,
Tobiko tests cases would use it. In case you want to make sure they use
a specific network please add reference to such network in
:ref:`tobiko-conf` file::

    [neutron]
    floating_network = public


Run Test Cases
--------------

Run Scenario Test Cases
~~~~~~~~~~~~~~~~~~~~~~~

Scenario test cases are in charge of creating workloads to simulate real use
of OpenStack. They create networks, virtual machines, ports, routers, etc.
They also tests these workloads are working.

Run Tobiko scenario test cases using Tox (it is going to take some minutes)::

    tox -e scenario

To list Heat stacks and Glance images created by test cases::

    tox -e venv -- openstack image list
    tox -e venv -- openstack stack list

Scenario test cases are also used to check if previously created resources are
still up and working as expected. To ensure test cases will not create those
resources again we can set `TOBIKO_PREVENT_CREATE` environment variable before
re-running test cases::

  TOBIKO_PREVENT_CREATE=yes tox -e scenario


Cleanup Tobiko Workloads
~~~~~~~~~~~~~~~~~~~~~~~~

Once Tobiko test cases have been executed we could want to clean up all
workloads left on the cloud so that we restore it to the original state.


Cleanup Heat Stacks
+++++++++++++++++++

Because Tobiko is using Heat stacks for orchestrating the creation of most of
the resources, by cleaning up all stacks created with Tobiko will clean it up
almost all::

  tox -e venv -- bash -c 'openstack stack list -f value -c ID | xargs openstack stack delete'


Cleanup Glance Images
+++++++++++++++++++++

Because Heat doen't support creation of Glance images, Tobiko implemented some
specific fixtures to download images from the Web and upload them to Glance
service::

    tox -e venv -- bash -c 'openstack stack list -f value -c ID | xargs openstack stack delete'


Run Disruptive Test Cases
~~~~~~~~~~~~~~~~~~~~~~~~~

Disruptive test cases are in charge of testing that after executing some type of
critical operation on the cloud, the services return working as expected after
a while. To execute them you can type::

    tox -e faults

The kind operations executed by these test cases could be cloud nodes reboot,
OpenStack services restart, virtual machines migrations, etc.

Please note that while scenario test cases are being executing in parallel to
speed up test case execution, faults test case are only executed sequentially.
This is because operation executed by such cases could break some functionality
for a short time and alter the regular state of the system expected from other
test cases to be executed.


Run the Tobiko Workflow
~~~~~~~~~~~~~~~~~~~~~~~

Scenario and disruptive test cases, being executed in a specify sequence could
be used to detect more problems on the cloud the disruptive test cases alone
are not looking for.

- First ensure there are workloads running fine by running scenario test cases::

    tox -e scenario

.. sidebar:: Note

    As second step we could instead update or upgrade OpenStack nodes.

- Second we could execute disruptive test cases to shake the system a bit::

    tox -e faults

- Third we could re-run scenario test cases to check things are still running
  as expected::

    TOBIKO_PREVENT_CREATE=yes tox -e scenario


Test Cases Report Files
~~~~~~~~~~~~~~~~~~~~~~~

After executing test cases we can look at more details regarding test case
results in a small set of files:

  - **test_results.html**:
    an user browseable HTML view of test case results
  - **test_results.log**:
    a log file with logging traces recollected from every individual test case
  - **test_results.subunit**:
    the original subunit binary file generated by test runner
  - **test_results.xml**:
    an XML Junit file to be used for example to show test cases result by
    Jenkins CI server

The name of above files can be changed from default value (*test_results*) to a
custom one by setting *TOX_REPORT_NAME* environment variable.

.. sidebar:: Legenda

    *{toxinidir}* stand for the Tobiko source files directory.

    *{envname}* is the name of the Tox enviroment to be executed (IE scenario,
    faults, etc.)

Above files are saved into a folder that can be specified with
*TOX_REPORT_DIR* environment variable.

By default the full path of report directory is made from below parts::

    {toxinidir}/report/{envname}
