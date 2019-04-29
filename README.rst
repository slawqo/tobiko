======
Tobiko
======


Test Big Cloud Operations
-------------------------

Tobiko is an OpenStack testing framework focusing on areas mostly
complementary to `Tempest <https://docs.openstack.org/tempest/latest/>`__.
While tempest main focus has been testing OpenStack rest APIs, the main Tobiko
focus would be to test OpenStack system operations while "simulating"
the use of the cloud as the final user would.

Tobiko's test cases populate the cloud with workloads such as instances, allows
the CI workflow to perform an operation such as an update or upgrade, and then
runs test cases to validate that the cloud workloads are still functional.


Main Project Goals
~~~~~~~~~~~~~~~~~~

- Provide a Python framework to write system scenario test cases;
- Provide CLI tools to implement a workflow designed to test potentially
  destructive operations (like cloud nodes reboot, update, upgrade...).
- Provide tools to monitor and recollect the healthy status of the cloud 


References
----------

* Free software: Apache License, Version 2.0
* Documentation: https://docs.openstack.org/tobiko/latest/
* Release notes: https://docs.openstack.org/releasenotes/tobiko/
* Source: https://opendev.org/x/tobiko
* Bugs: https://storyboard.openstack.org/#!/project/x/tobiko
