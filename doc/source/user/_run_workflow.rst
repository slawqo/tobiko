Scenario and disruptive test cases, which are being executed in a specific
sequence, could be used to uncover more issues with the cloud than disruptive
test cases alone.

- First ensure there are workloads properly running by running scenario test cases::

    tox -e scenario

.. sidebar:: Note

    As second step we may, instead, update or upgrade OpenStack nodes.

- Next we could execute disruptive test cases to "stress" the cloud::

    tox -e faults

- Finally we might re-run scenario test cases to check that everything is still running
  as expected::

    TOBIKO_PREVENT_CREATE=yes tox -e scenario
