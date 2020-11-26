==========
Tobiko 0.3
==========


Test Big Cloud Operations
-------------------------

Tobiko is an OpenStack testing framework focusing on areas mostly
complementary to `Tempest <https://docs.openstack.org/tempest/latest/>`__.
While tempest main focus has been testing OpenStack rest APIs, the main Tobiko
focus is to test OpenStack system operations while "simulating"
the use of the cloud as the final user would.

Tobiko's test cases populate the cloud with workloads such as Nova instances;
they execute disruption operations such as services/nodes restart; finally they
run test cases to validate that the cloud workloads are still functional.

Tobiko's test cases can also be used, for example, for testing that previously
created workloads are working right after OpenStack services update/upgrade
operation.


Project Requirements
--------------------

Tobiko Python framework is being automatically tested with below Python
versions:

- Python 3.6
- Python 3.8
- Python 3.9 (new)

and below Linux distributions:

- CentOS 7 / RHEL 7 (with Python 3.6)
- CentOS 8 / RHEL 8 (with Python 3.6)
- Ubuntu Focal (with Python 3.8)

Tobiko has also been tested for development purposes with below OSes:

- Fedora 31 (with Python 3.7)
- Fedora 32 (with Python 3.8)
- Fedora 33 (with Python 3.9)
- OSX (with Python 3.6 and Python 3.8)
- Ubuntu Bionic (with Python 3.6)
- Ubuntu Focal (with Python 3.9)

The Tobiko Python framework is being used to implement test cases. As Tobiko
can be executed on nodes that are not part of the cloud to test against, this
doesn't mean Tobiko requires cloud nodes have to run with one of above Python
versions or Linux distributions.


Main Project Goals
~~~~~~~~~~~~~~~~~~

- To test OpenStakc and Red Hat OpenStack Platform projects before they are
  released.
- To provide a Python framework to write system scenario test cases (create
  and test workloads), to write white boxing test cases (to log to cloud nodes
  for internal inspection purpose), to write disruptive test cases (to simulate
  service disruptions like for example rebooting/interrupting a service to
  verify cloud reliability).
- To provide Ansible roles to implement a work-flow designed to run an ordered
  sequence of test cases groups (like for example tests that creates resources
  and verify they are working, tests that execute cloud disruptions, and finally
  tests that verify if resources initially created are still working). The main
  use of these roles is writing continuous integration jobs for Zuul (via bare
  Ansible roles) or other services like Jenkins (via the InfraRed plug-in).
- To verify previously created workloads are working fine after executing
  OpenStack nodes update/upgrade.
- To provide tools to monitor and recollect the healthy status of the cloud as
  seen from user perspective (black-box testing) or from inside (white-box
  testing).


References
----------

* Free software: Apache License, Version 2.0
* Documentation: https://tobiko.readthedocs.io/en/latest/
* Release notes: https://docs.openstack.org/releasenotes/tobiko/
* Source code: https://opendev.org/x/tobiko
* Bugs: https://storyboard.openstack.org/#!/project/x/tobiko


Related projects
~~~~~~~~~~~~~~~~
* OpenStack: https://www.openstack.org/
* Red Hat OpenStack Platform: https://www.redhat.com/en/technologies/linux-platforms/openstack-platform
* Python: https://www.python.org/
* Testtools: https://github.com/testing-cabal/testtools
* Ansible: https://www.ansible.com/
* InfraRed: https://infrared.readthedocs.io/en/latest/
* DevStack: https://docs.openstack.org/devstack/latest/
* Zuul: https://docs.openstack.org/infra/system-config/zuul.html
* Jenkins: https://www.jenkins.io/
