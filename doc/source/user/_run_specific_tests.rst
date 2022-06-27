In the first terminal, execute some Tobiko test cases as below:

To run test cases you need a test runner able to execute Python test cases.
Test cases delivered with Tobiko has been tested using
`stestr <https://stestr.readthedocs.io/en/latest/>`__

From the Tobiko source folder you can run scenario test cases using the below command::

    pytest tobiko/tests/scenario/

You could also use tox to run test cases::

    tox -e <environment_variable> -- path/to/test/module

For example::

    tox -e scenario -- tobiko/tests/scenario/neutron/test_router.py

Note that with tox, the <environment_variable> should match the directory where
the test is (if the test is inside the 'scenario' directory, the environment
variable has to be scenario).


You can also run only a class of test cases by running::

    tox -e <tox-env-list> -- path/to/test/module::class

You can run only a specific test case (a method) by running::

    tox -e <tox-env-list> -- path/to/test/module::class::test_case
