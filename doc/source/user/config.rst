.. _tobiko-configuration-guide:

==========================
Tobiko Configuration Guide
==========================


Document Overview
-----------------

This document describes how to configure Tobiko.

.. sidebar:: See also

    For a quick and simpler start you can jump to the
    :ref:`tobiko-quick-start-guide`.

    To install Tobiko inside a virutalenv please read
    :ref:`tobiko-installation-guide`.

    To run Tobiko scenario test cases please look at
    :ref:`tobiko-test-case-execution-guide`.


Configure Tobiko Framework
--------------------------

In order to make sure Tobiko tools can connect to OpenStack services via Rest
API configuration parameters can be passed either via environment variables or
via a ini configuration file (referred here as :ref:`tobiko-conf`). Please look
at :ref:`authentication-methods` for more details.

To be able to execute scenario test cases there some OpenStack resources that
has to be created before running test cases. Please look at
:ref:`setup-required-resources` for more details.


.. _tobiko-conf:

tobiko.conf
~~~~~~~~~~~

Tobiko tries to load :ref:`tobiko-conf` file from one of below locations:

* current directory::

    ./tobiko.conf

* user home directory::

    ~/.tobiko/tobiko.conf

* system directory::

    /etc/tobiko/tobiko.conf


Configure Logging
~~~~~~~~~~~~~~~~~

Tobiko can configure logging system to write messages to a log file. You can
edit below options in :ref:`tobiko-conf` to enable it as below::

    [DEFAULT]
    # Whenever to allow debugging messages to be written out or not
    debug = true

    # Name of the file where log messages will be appended.
    log_file = tobiko.log

    # The base directory used for relative log_file paths.
    log_dir = .


.. _authentication-methods:


Authentication Methods
~~~~~~~~~~~~~~~~~~~~~~

Tobiko uses
`OpenStack client <https://docs.openstack.org/python-openstackclient/latest/>`__
to connect to OpenStack services.


.. _authentication-environment-variables:

Authentication Environment Variables
++++++++++++++++++++++++++++++++++++

To configure how Tobiko can connect to
services you can use the same
`environment variables <https://docs.openstack.org/python-openstackclient/latest/cli/man/openstack.html#environment-variables>`__
you would use for OpenStack Python client CLI.

Currently supported variables are::

    # Identity API version
    export OS_IDENTITY_API_VERSION=3

    # URL to be used to connect to OpenStack Irentity Rest API service
    export OS_AUTH_URL=http://10.0.0.109:5000/v3

    # Authentication username (name or ID)
    export OS_USERNAME=admin
    export OS_USER_ID=...

    # Authentication password
    export OS_PASSWORD=...

    # Project-level authentication scope (name or ID)
    export OS_PROJECT_NAME=admin
    export OS_TENANT_NAME=admin
    export OS_PROJECT_ID=...
    export OS_TENANT_ID=...

    # Domain-level authorization scope (name or ID)
    export OS_DOMAIN_NAME=Default
    export OS_DOMAIN_ID=...

    # Domain name or ID containing user
    export OS_USER_DOMAIN_NAME=Default
    export OS_USER_DOMAIN_ID=...

    # Domain name or ID containing project
    export OS_PROJECT_DOMAIN_NAME=Default
    export OS_PROJECT_DOMAIN_ID=...

    # ID of the trust to use as a trustee user
    export OS_TRUST_ID=...


.. _authentication-configuration:

Autentication Configuration
+++++++++++++++++++++++++++

You can also configure the same authentication parameters by editing 'keystone'
section in :ref:`tobiko-conf` file. For example::

    [keystone]
    # Identity API version
    api_version = 3

    # URL to be used to connect to OpenStack Irentity Rest API service
    auth_url=http://10.0.0.109:5000/v3

    # Authentication username (name or ID)
    username = admin

    # Authentication password
    password = ...

    # Project-level authentication scope (name or ID)
    project_name = admin

    # Domain-level authorization scope (name or ID)
    domain = default

    # Domain name or ID containing user
    user_domain_name = default

    # Domain name or ID containing prject
    project_domain_name = default

    # ID of the trust to use as a trustee user
    trust_id = ...


.. _proxy-server-configuration:

Proxy Server Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

The first thing to make sure is Tobiko can reach OpenStack services. In case
OpenStack is not directly accessible from where test cases or Tobiko CLI are
executed it is possible to use an HTTP proxy server running on a network that
is able to reach all OpenStack Rest API service. This can be performed
by using below standard environment variables::

    export http_proxy=http://<proxy-host>:<proxy-port>/
    export https_proxy=http://<proxy-host>:<proxy-port>/
    export no_proxy=127.0.0.1,...

For convenience it is also possible to specify the same parameters via
:ref:`tobiko-conf`::

    [http]
    http_proxy = http://<proxy-host>:<proxy-port>/
    https_proxy = http://<proxy-host>:<proxy-port>/
    no_proxy = 127.0.0.1,...

Because Tobiko test cases could execute local commands (like for example ping)
to reach network services we have to specify in tobiko.conf file a shell
(like OpenSSH client) to be used instead of the default local one
('/bin/sh')::

    [shell]
    command = /usr/bin/ssh <proxy-host>

Please make sure it is possible to execute commands on local system without
having to pass a password::

    /usr/bin/ssh <proxy-host> echo 'Yes it works!'

To archive it please follow one of the
`many guides available on Internet
<https://www.google.com/search?q=passwordless+ssh&oq=passwordless+&aqs=chrome.0.0j69i57j0l4.4775j0j7&sourceid=chrome&ie=UTF-8>`__
.


.. _setup-required-resources:

Setup Required Resources
~~~~~~~~~~~~~~~~~~~~~~~~

To be able to execute Tobiko scenario test cases there some OpenStack
resources that has to be created before running test cases.

Install required Python OpenStack clients::

    pip install --upgrade \
        -c https://opendev.org/openstack/requirements/raw/branch/master/upper-constraints.txt \
        python-openstackclient \
        python-neutronclient

You need to make sure :ref:`authentication-environment-variables` are properly
set::

    source openstackrc
    openstack network list


Add reference to the network where Tobiko should create floating IP instances
in :ref:`tobiko-conf` file::

    [neutron]
    floating_network = public


Skipping resources creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In some cases, for example when Tobiko is run after upgrade of cloud, it may be expected
that resources used for tests should be already created. Tobiko should not try to create
resources than and just run tests using what is already created.
To configure Tobiko to not create test resources, environment variable ``TOBIKO_PREVENT_CREATE``
can be used::

    export TOBIKO_PREVENT_CREATE=True

If this is set to ``True`` or ``1`` then Tobiko will not try to create resources like VMs,
networks, routers or images and just run validation of what is exists in the cloud already.

What's Next
-----------

To know how to run Tobiko scenario test cases you can look at
:ref:`tobiko-test-case-execution-guide`
