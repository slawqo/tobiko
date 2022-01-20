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

Run Test Cases
--------------

The next section is a quick guide about running some test cases.
For more information, please see our
:ref:`Tobiko Test Cases Execution Guide<tobiko-test-case-execution-guide>`

Before running test cases, make sure you
:ref:`configure tobiko logging <conf_logging>` according to
your needs.

.. note::
    Unlike other testing frameworks, **Tobiko does not delete its**
    **resources after test cases finish their execution**.
    You may clean up tobiko workloads after the execution manually, for example
    heat stacks and glance images.

Run Scenario Test Cases
~~~~~~~~~~~~~~~~~~~~~~~

.. include:: _run_scenario.rst

Run Disruptive Test Cases
~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: _run_faults.rst

Run the Tobiko Workflow
~~~~~~~~~~~~~~~~~~~~~~~

.. include:: _run_workflow.rst

Test Cases Report Files
~~~~~~~~~~~~~~~~~~~~~~~

.. include:: _test_cases_report_files.rst
