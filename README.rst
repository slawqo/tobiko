======
Tobiko
======

Tobiko is an OpenStack testing framework focusing on areas
complementary to Tempest:

- Minor updates and major upgrades. Tobiko tests populate the
  cloud with workloads such as instances, allows the CI workflow
  to perform an operation such as an update or upgrade, and then runs
  tests that validate that the cloud workloads are still functional.
- Fault injection, like restarting nodes, OpenStack services and
  dependencies such as OVS, RabbitMQ or the DB.
- White box testing; Specifically the ability to run commands on
  nodes.

Links
~~~~~

* Documentation: `Tobiko Documentation <https://docs.openstack.org/tobiko/latest/>`__
* Usage: `Tobiko User Guide <https://docs.openstack.org/tobiko/latest/user/>`__
* Bugs: `Tobiko StoryBoard <https://storyboard.openstack.org/#!/project/x/tobiko>`__
* Source Code: https://opendev.org/x/tobiko.git
* License: `Apache License v2.0 <https://opendev.org/x/tobiko/src/branch/master/LICENSE>`__
