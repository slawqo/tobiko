.. _tobiko-from-tempest-to-tobiko:

======================
From Tempest to Tobiko
======================

*This doc might help programmers to embrace/join the Tobiko project, after having some experience with the Tempest project.*


A few differences between Tobiko and Tempest:
---------------------------------------------
* Tobiko uses heat template stacks
    * A `stack <https://docs.openstack.org/heat/latest/index.html>`_ is being created *"lazily"* (only when it is needed in the code), unlike “resource setup” in Tempest that always creates all the resources.

* Tobiko re-uses its resources
    * Tobiko will reuse the same resources in any possible test it can.

      Ex: if one test will create a stack, and the same stack is going to be used in different tests, Tobiko will simply reuse it. It will also reuse the same stacks during other executions of the same Tobiko tests.

* Tobiko’s tests structure:
    * Tests do not require idempotent_id, each method which starts with the prefix “test” is considered to be a test which will be run.
    * After a Tobiko test suite finishes, it **does not** delete Tobiko’s resources (no teardown), and this is by design.

* Tobiko uses a client stack
    * Traffic is being sent from a client stack that the tester may create (or a default one might be created).

* Tobiko uses `Typing <https://docs.python.org/3/library/typing.html>`_:
    * Mainly as a means of code readability and consistency.

      But additional doc strings are welcome!

* Tobiko tests workflow:
    * Tobiko uses the following workflow for its sequential test execution process:

      resource-creation->disruptive-actions->resource-verification.
