.. _tobiko-quick-start-guide:

===========
Quick Start
===========

This document describes how to setup an environment and how to run test cases

.. sidebar:: See also

    To install Tobiko inside a virutalenv please read
    :ref:`tobiko-installation-guide`.

    To configure Tobiko please read :ref:`tobiko-configuration-guide`.

    To run Tobiko scenario test cases please look at
    :ref:`tobiko-test-case-execution-guide`.


.. include:: _install_venv.rst


Configure tobiko with tobiko.conf
---------------------------------

.. include:: _conf_explanation.rst
    :start-after: tobiko-conf-label

Configure Logging Options
-------------------------

.. include:: _conf_logging.rst
    :start-after: configure-tobiko-logging-label

.. include:: _conf_credentials.rst

.. _generating-venv-with-tox:

Create a virtual environment with tox
-------------------------------------

.. include:: _conf_venv_with_tox.rst

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


Cleaning Up Tobiko Workloads
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once Tobiko test cases have been executed, we may want to clean up all
workloads remaining on the cloud so that we restore it to its original state.


Cleaning Up Heat Stacks
++++++++++++++++++++++++

Because Tobiko is using Heat stacks for orchestrating the creation of most of
the resources, deleting all stacks created with Tobiko will clean up
almost all resources::

  tox -e venv -- bash -c 'openstack stack list -f value -c ID | xargs openstack stack delete'


Cleaning Up Glance Images
++++++++++++++++++++++++++

Because Heat doesn't support creation of Glance images, Tobiko implements some
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

- Finally we might re-run scenario test cases to check that everything is still running
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
