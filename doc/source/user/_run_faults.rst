Disruptive (or faults) test cases are used for testing that after inducing some critical
disruption to the operation of the cloud, the services can get back to the expected state
after a while. To execute them you can type::

    tox -e faults

The faults induced by these test cases could be cloud nodes reboot,
OpenStack services restart, virtual machines migrations, etc.

Please note that while scenario test cases are being executed in parallel (to
speed up test case execution), disruptive test cases are only executed sequentially.
This is because the operations executed by such cases could break some functionality
for a short time and alter the regular state of the system which may be assumed by other
test cases to be executed.
