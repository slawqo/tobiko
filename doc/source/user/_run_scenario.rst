Scenario test cases are used to create workloads that simulate real-world use
of OpenStack. They create networks, virtual machines, ports, routers, etc.
They also validate that these workloads are functioning.

Running Tobiko scenario test cases using Tox (may take some minutes to complete)::

    tox -e scenario

Scenario test cases are also used to check that previously created resources are
still up and working as expected. To ensure test cases will not create those
resources again we can set `TOBIKO_PREVENT_CREATE` environment variable before
re-running test cases::

  TOBIKO_PREVENT_CREATE=yes tox -e scenario
