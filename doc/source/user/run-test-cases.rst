.. _tobiko-test-case-execution-guide:

=================================
Tobiko Test Cases Execution Guide
=================================

This document describes how to execute Tobiko scenario test cases.

.. sidebar:: See also

    For a quick and simpler start you can jump to the
    :ref:`tobiko-quick-start-guide`.

    To install Tobiko inside a virutalenv please read
    :ref:`tobiko-installation-guide`.

    To configure Tobiko please read :ref:`tobiko-configuration-guide`.


Prepare Your System
~~~~~~~~~~~~~~~~~~~

Before running Tobiko test cases you need to be sure you are doing it from
Tobiko source files folder and that you have actived a Virtualenv where Tobiko
and its requirements are installed. Please refers to
:ref:`tobiko-installation-guide` and :ref:`tobiko-configuration-guide` to know
how to setup your system before running test cases.


Run Scenario Test Cases
~~~~~~~~~~~~~~~~~~~~~~~

To run test cases you need a test runner able to execute Python test cases.
Test cases delivered with Tobiko has been tested using
`stestr <https://stestr.readthedocs.io/en/latest/>`__

From Tobiko source folder you can run scenario test cases using below command::

    stestr run --test-path tobiko/tests/scenario/
