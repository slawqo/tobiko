.. _tobiko-faults-execution-guide:

=================================
Tobiko Faults Execution Guide
=================================

This document describes how to execute faults with Tobiko.

.. sidebar:: See also

    For a quick and simpler start you can jump to the
    :ref:`tobiko-quick-start-guide`.

    To install Tobiko inside a virutalenv please read
    :ref:`tobiko-installation-guide`.

    To configure Tobiko please read :ref:`tobiko-configuration-guide`.


Requirements
~~~~~~~~~~~~

In order to be able faults with Tobiko you need an RC file
for your OpenStack hosts (not the instances which run on OpenStack hosts)
Using this RC file, Tobiko will be able to generate an os-faults configuration
for you automatically. If you already have os-faults configuration file, you
don't need this requirement.

CLI
~~~

In order to restart openvswitch service, run the following command:

    tobiko-fault "restart openvswitch service"

Python API
~~~~~~~~~~
You can also use faults in your tests. Warning: running a fault in a test
while other tests are running in parallel might have negative affect on your
other tests.

    from tobiko.fault.executor import FaultExecutor
    fault = FaultExecutor()
    fault.execute("restart openvswitch service")

Missing services & containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

What to do if the service or the container I'm trying to control
is not part of os-faults configuration? In that case please submit a patch
to Tobiko to add it to tobiko/fault/templates/os-faults.yml.j2 template.
